"""Bằng chứng checkpoint và mô phỏng contract offline cho demo."""
import json
from pathlib import Path
import subprocess

from agent import run_agent
from status_tools import StatusTools

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = 'https://github.com/manhtuongqt/K5-L3A-DAY04-NguyenManhTuong-2A202603646-ReactLoopAgent'


def read_json(path, default=None):
    file = ROOT / path
    return json.loads(file.read_text(encoding='utf-8')) if file.exists() else default


def submission_state():
    def git(*args):
        result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ''
    commit = git('rev-parse', 'HEAD')
    remote = git('rev-parse', 'origin/main')
    clean = not git('status', '--porcelain')
    return {'repo_url': REPO_URL, 'commit': commit,
            'pushed': bool(commit and commit == remote and clean),
            'lms_submitted': False}


def lab_report():
    before, after = read_json('eval_before.json'), read_json('eval_after.json')
    audit = read_json('artifacts/checkpoint_audit.json', {})
    return {'gates': audit.get('gates', []), 'before': before, 'after': after,
            'comparison': read_json('artifacts/cp6_comparison.json'),
            'unit_tests': audit.get('unit_tests', read_json('artifacts/cp5_improved/manifest.json', {}).get('unit_tests', {})),
            'submission': submission_state()}


def evidence(phase, case_id):
    if phase not in ('before', 'after'):
        raise ValueError('Sai phiên bản eval.')
    report = read_json('eval_' + phase + '.json')
    if not report:
        raise ValueError('Lần eval này chưa hoàn tất.')
    case = next((c for c in report['cases'] if c['id'] == case_id), None)
    if not case:
        raise ValueError('Không có case này.')
    result = case['result']
    return {'kind': 'saved', 'phase': phase, 'case_id': case_id,
            'question': case['question'], 'model': case['model'], 'result': result,
            'checks': {'completed': result['status'] == 'completed',
                       'tool_called': any(e.get('event') == 'tool' for e in result['trace']),
                       'tool_results_linked': None, 'all_calls_returned': None}}


def call(arguments='{"provider":"github"}', name='get_status', call_id='offline-1'):
    return {'message': {'role': 'assistant', 'content': None, 'tool_calls': [
        {'id': call_id, 'type': 'function', 'function': {'name': name, 'arguments': arguments}}]},
        'calls': [{'id': call_id, 'name': name, 'arguments': arguments}],
        'finish': 'tool_calls', 'usage': {}}


def final(text, finish='stop'):
    return {'message': {'role': 'assistant', 'content': text}, 'calls': [],
            'finish': finish, 'usage': {}}


class ScriptedProvider:
    def __init__(self, responses):
        self.responses, self.histories = iter(responses), []

    def complete(self, messages, schemas):
        self.histories.append(list(messages))
        return next(self.responses)


def contract_case(case_id):
    tools, budget = StatusTools('snapshot'), 6
    if case_id == 'invalid_json':
        question = 'Mô phỏng arguments sai JSON, rồi sửa và tiếp tục.'
        responses = [call('{'), call(), final('Đã sửa arguments và nhận trạng thái từ tool.')]
    elif case_id == 'length':
        question = 'Mô phỏng output model bị cắt.'
        responses = [final('Câu trả lời chưa hoàn chỉnh', 'length')]
    elif case_id == 'timeout':
        question = 'Mô phỏng tool timeout; không kết luận dịch vụ outage.'
        tools = StatusTools('snapshot', fail=True)
        responses = [call(), final('Không lấy được dữ liệu do tool timeout; chưa đủ bằng chứng kết luận trạng thái dịch vụ.')]
    elif case_id == 'max_steps':
        question, budget = 'Mô phỏng model cần tiếp tục nhưng chỉ có một bước.', 1
        responses = [call()]
    elif case_id == 'missing_source':
        question = 'Mô phỏng câu trả lời thiếu URL sau khi đọc incident thành công.'
        details = tools.get_incident_details('github', 'xr3myzj7ms51')
        responses = [call('{"provider":"github","incident_id":"xr3myzj7ms51"}', 'get_incident_details'),
                     final('Incident đã được xử lý.'), final('Incident đã được xử lý. Nguồn: ' + details['url'])]
    else:
        raise ValueError('Không có tình huống offline này.')
    provider = ScriptedProvider(responses)
    result = run_agent(question, provider, tools, max_steps=budget)
    expected_status = {'length': 'error', 'max_steps': 'max_steps'}.get(case_id, 'completed')
    return {'kind': 'contract', 'label': 'Mô phỏng offline, không gọi API',
            'expected_status': expected_status,
            'contract_passed': result['status'] == expected_status,
            'question': question, 'model': 'FakeProvider (offline)', 'result': result,
            'checks': {'completed': result['status'] == 'completed',
                       'tool_called': any(e.get('event') == 'tool' for e in result['trace']),
                       'tool_results_linked': None, 'all_calls_returned': None}}
