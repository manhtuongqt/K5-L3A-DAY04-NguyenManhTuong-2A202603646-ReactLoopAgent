"""Tự đối chiếu bằng chứng kỹ thuật, không tự xác nhận đã nộp LMS."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from demo.support import contract_case, REPO_URL


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def metrics(report):
    return {
        'agent_calls': sum(len(c['result']['usage']) for c in report['cases']),
        'tool_calls': sum(sum(e.get('event') == 'tool' for e in c['result']['trace']) for c in report['cases']),
        'tokens': sum(sum(u.get('total_tokens', 0) for u in c['result']['usage'])
                      + c['grade'].get('judge_usage', {}).get('total_tokens', 0) for c in report['cases']),
    }


def main():
    before = read('eval_before.json')
    after = read('eval_after.json') if (ROOT / 'eval_after.json').exists() else None
    baseline = read('artifacts/cp3_baseline/manifest.json')
    code = read('artifacts/cp5_improved/manifest.json')
    artifacts = ROOT / 'artifacts'
    with (artifacts / 'final_unit_tests.txt').open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.discover(str(ROOT / 'tests')))
    units = {'total': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors),
             'failures': len(result.failures), 'errors': len(result.errors)}
    tests_pass = not result.failures and not result.errors
    source_gate = contract_case('missing_source')['result']
    source_pass = source_gate['status'] == 'completed' and any(
        e['event'] == 'validation_missing_source' for e in source_gate['trace'])
    protected = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
                 for path, sha in baseline['protected_sha256'].items()}
    code_frozen = all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
                      for path, sha in code['files'].items())
    before_complete = len(before['cases']) == 22 and before['summary']['scored_cases'] == 22 and before['summary']['score_0_100'] is not None
    after_complete = bool(after and len(after['cases']) == 22 and after['summary']['scored_cases'] == 22 and after['summary']['score_0_100'] is not None)
    same_config = bool(after and before['config'] == after['config'])
    if after:
        bm, am = metrics(before), metrics(after)
        old = {c['id']: c for c in before['cases']}
        comparison = {
            'score_before': before['summary']['score_0_100'],
            'score_after': after['summary']['score_0_100'],
            'score_delta': round(after['summary']['score_0_100'] - before['summary']['score_0_100'], 2) if after_complete else None,
            'config_equal': same_config,
            **{name + '_before': value for name, value in bm.items()},
            **{name + '_after': value for name, value in am.items()},
            'cases': [{'id': c['id'], 'before': old[c['id']]['grade']['score'],
                       'after': c['grade']['score'],
                       'delta': c['grade']['score'] - old[c['id']]['grade']['score'] if c['grade']['score'] is not None else None}
                      for c in after['cases']],
            'currency_cost': None,
            'currency_cost_note': 'Gateway cost field has no verified currency/unit; do not report USD.',
        }
        # UI spec uses these readable aliases.
        comparison['agent_calls_before'] = bm['agent_calls']
        comparison['agent_calls_after'] = am['agent_calls']
        (artifacts / 'cp6_comparison.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    gates = [
        {'id': 'CP1', 'title': 'Setup và khám phá tools', 'status': 'passed',
         'work': 'Fork đúng tên L3A, cấu hình model CKEY và chạy hai status tools.',
         'criteria': 'Tool trả JSON; có API run thật và repo riêng.',
         'detail': 'Model claude-opus-5; key ngoài Git. Quyền push được xác minh ở bước phát hành.',
         'evidence': ['artifacts/cp2/cp2_ckey_opus_run.json', 'docs/checkpoints/CP2_HUONG_DAN.md']},
        {'id': 'CP2', 'title': 'Agent loop', 'status': 'passed' if tests_pass else 'pending',
         'work': 'Giữ assistant message, trả đúng ID cho mọi tool call, gọi model tiếp đến khi dừng.',
         'criteria': 'Câu hỏi thật completed; tests ID và nhiều calls đạt.',
         'detail': 'Có thể thử API thật trong tab CP2; snapshot không phải trạng thái live.',
         'evidence': ['agent.py', 'artifacts/cp2/cp2_ckey_opus_run.json', 'artifacts/final_unit_tests.txt']},
        {'id': 'CP3', 'title': 'Xử lý lỗi và trace', 'status': 'passed' if tests_pass else 'pending',
         'work': 'Giới hạn bước, lỗi JSON/tool/provider, output bị cắt và trace.',
         'criteria': 'Không crash; lỗi trả observation hoặc kết thúc đúng; chỉ báo completed không thay thế độ đúng.',
         'detail': f"Bản CP3: 41/43, còn hai tests nguồn CP5. Bản cuối: {units['passed']}/{units['total']} tests đạt.",
         'evidence': ['docs/checkpoints/CP3_DANH_GIA.md', 'tests/test_cp3.py', 'artifacts/final_unit_tests.txt']},
        {'id': 'CP4', 'title': 'Eval lần đầu', 'status': 'passed' if before_complete else 'pending',
         'work': 'Chạy đủ 22 case, đọc reason/mechanical/trace và lập danh sách lỗi.',
         'criteria': '22/22 được chấm và summary.score_0_100 khác null.',
         'detail': '96,73/100; H3 50/100 do chưa tra trực tiếp ID incident.',
         'evidence': ['eval_before.json', 'docs/checkpoints/CP4_DANH_GIA.md', 'NOTES.md']},
        {'id': 'CP5', 'title': 'Phân tích và cải tiến', 'status': 'passed' if tests_pass and source_pass else 'pending',
         'work': 'Sửa prompt tra ID cụ thể; loop kiểm tra URL đã quan sát, yêu cầu sửa trong cùng budget.',
         'criteria': 'NOTES mục 1–3 có bằng chứng/thay đổi; toàn bộ tests đạt.',
         'detail': 'URL validation không chứng minh mọi claim đúng. Không sửa dataset, fixtures hay grading.',
         'evidence': ['agent.py', 'docs/checkpoints/CP5_DANH_GIA.md', 'NOTES.md', 'artifacts/cp5_improved/manifest.json']},
        {'id': 'CP6', 'title': 'Eval sau cải tiến', 'status': 'passed' if after_complete and same_config and code_frozen and all(protected.values()) else 'pending',
         'work': 'Chạy lại cùng cấu hình; so sánh điểm, lỗi, model calls và token.',
         'criteria': '22/22 được chấm, config trước/sau giống nhau, NOTES mục 4–5 hoàn chỉnh.',
         'detail': 'Một lượt mỗi bản không chứng minh ổn định; đọc cả hồi quy và cải thiện.',
         'evidence': ['eval_after.json', 'artifacts/cp6_comparison.json', 'docs/checkpoints/CP6_DANH_GIA.md', 'NOTES.md']},
        {'id': 'CP7', 'title': 'Demo, push và nộp', 'status': 'partial',
         'work': 'Demo trace nhiều bước, lỗi H3 thật trước sửa, báo cáo và repo để nộp.',
         'criteria': 'Demo giải thích được; repo public đúng tên, push đầy đủ; người học tự nộp link LMS.',
         'detail': 'Có demo và bằng chứng kỹ thuật; trạng thái push hiển thị theo Git. Chưa xác nhận nộp LMS hoặc trình bày với trợ giảng.',
         'evidence': ['docs/checkpoints/CP7_NOP_BAI.md', 'demo/README.md', REPO_URL]},
    ]
    audit = {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'unit_tests': units,
             'protected_unchanged': protected, 'improved_code_frozen': code_frozen,
             'config_equal': same_config, 'gates': gates,
             'lms_submitted': False, 'classroom_demo_verified': False}
    (artifacts / 'checkpoint_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'unit_tests': units, 'gates': {g['id']: g['status'] for g in gates}}))
    return 0 if tests_pass else 1


if __name__ == '__main__':
    sys.exit(main())
