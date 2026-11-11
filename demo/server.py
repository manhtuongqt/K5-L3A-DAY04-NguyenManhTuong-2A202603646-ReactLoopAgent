"""Demo CP2 cục bộ: quan sát loop hiện có, không sửa agent hoặc eval."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import threading
import sys
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import run_agent
from providers import Provider
from status_tools import StatusTools
from demo.support import lab_report, evidence, contract_case

RUN_LOCK = threading.Lock()
CASES = [
    {'id': 'cp2_status', 'title': '01 · Một tool',
     'question': 'Kiểm tra trạng thái GitHub Actions theo snapshot bằng get_status. Nêu mốc dữ liệu và nguồn.',
     'expectation': 'Model gọi get_status, nhận kết quả và trả lời.'},
    {'id': 'cp2_investigate', 'title': '02 · Điều tra hai bước',
     'question': 'Kiểm tra Cloudflare Cache Purge theo snapshot. Sau khi lấy danh sách, đọc chi tiết một incident liên quan bằng get_incident_details rồi nêu phạm vi ảnh hưởng, mốc dữ liệu và URL nguồn.',
     'expectation': 'Quan sát get_status → get_incident_details → trả lời có nguồn.'},
    {'id': 'cp2_multi', 'title': '03 · Hai nhà cung cấp',
     'question': 'Dùng tools kiểm tra trạng thái GitHub và Cloudflare theo snapshot. Đối chiếu trạng thái, mốc dữ liệu và nguồn của từng nhà cung cấp.',
     'expectation': 'Cả hai nhà cung cấp được kiểm tra. Model có thể gọi song song trong một lượt hoặc qua nhiều lượt.'},
]


def redact(value):
    text = json.dumps(value, ensure_ascii=False)
    for name, secret in os.environ.items():
        if any(part in name.upper() for part in ('API_KEY', 'TOKEN', 'SECRET')) and len(secret) > 10:
            text = text.replace(secret, '[REDACTED]')
    text = re.sub(r'sk-[A-Za-z0-9_-]{15,}', '[REDACTED]', text)
    return json.loads(text)


class ObservedProvider:
    def __init__(self, provider, emit):
        self.provider, self.emit = provider, emit
        self.step = 0
        self.pending = []
        self.generated = self.verified = 0
        self.linked = self.returned = True

    def complete(self, messages, schemas):
        self.step += 1
        tool_messages = []
        if self.pending:
            for message in reversed(messages):
                if message['role'] != 'tool':
                    break
                tool_messages.append(message)
            actual = [m.get('tool_call_id') for m in reversed(tool_messages)]
            expected = [c['id'] for c in self.pending]
            self.linked &= actual == expected
            self.returned &= len(actual) == len(expected) and set(actual) == set(expected)
            self.verified += len(expected)
        else:
            actual = []
        self.emit({'event': 'model_start', 'step': self.step, 'tool_result_ids': actual})
        response = self.provider.complete(messages, schemas)
        self.pending = response.get('calls', [])
        self.generated += len(self.pending)
        self.emit({'event': 'model_result', 'step': self.step,
                   'finish': response.get('finish'), 'calls': self.pending})
        return response

    def checks(self, result):
        verified = self.generated > 0 and self.generated == self.verified
        return {
            'completed': result['status'] == 'completed',
            'tool_called': any(e.get('event') == 'tool' for e in result['trace']),
            'tool_results_linked': self.linked if verified else None,
            'all_calls_returned': self.returned if verified else None,
        }


class ObservedTools:
    def __init__(self, emit):
        self.tools, self.emit = StatusTools('snapshot'), emit

    def execute(self, name, args):
        self.emit({'event': 'tool_start', 'name': name, 'arguments': args})
        result = self.tools.execute(name, args)
        self.emit({'event': 'tool_result', 'name': name, 'result': result})
        return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not log user questions or query strings.
        pass

    def reply(self, status, body, content_type='application/json; charset=utf-8'):
        data = body.encode('utf-8') if isinstance(body, str) else json.dumps(redact(body), ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.reply(200, (ROOT / 'demo' / 'index.html').read_text(encoding='utf-8'), 'text/html; charset=utf-8')
        elif self.path == '/api/config':
            self.reply(200, {'model': os.getenv('MODEL', ''), 'mode': 'snapshot',
                             'cases': CASES, 'replay_available': (ROOT / 'artifacts/cp2/cp2_ckey_opus_run.json').exists()})
        elif self.path == '/api/lab':
            self.reply(200, lab_report())
        elif urlsplit(self.path).path == '/api/evidence':
            query = parse_qs(urlsplit(self.path).query)
            try:
                self.reply(200, evidence(query.get('phase', ['before'])[0], query.get('case', ['H3'])[0]))
            except ValueError as exc:
                self.reply(404, {'message': str(exc)})
        elif self.path == '/api/replay':
            result = json.loads((ROOT / 'artifacts/cp2/cp2_ckey_opus_run.json').read_text(encoding='utf-8'))
            self.reply(200, {'kind': 'saved', 'model': 'claude-opus-5',
                            'question': 'Kiểm tra GitHub Actions bằng get_status, sau đó đọc chi tiết một incident liên quan bằng get_incident_details. Nêu mốc snapshot, phạm vi và URL nguồn.',
                            'result': result, 'checks': {'completed': result['status'] == 'completed',
                             'tool_called': any(e.get('event') == 'tool' for e in result['trace']),
                             'tool_results_linked': None, 'all_calls_returned': None}})
        else:
            self.reply(404, {'message': 'Không tìm thấy.'})

    def do_POST(self):
        if self.path not in ('/api/run', '/api/contract'):
            self.reply(404, {'message': 'Không tìm thấy.'})
            return
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:8504', 'http://localhost:8504'):
            self.reply(403, {'message': 'Chỉ nhận yêu cầu từ demo cục bộ.'})
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 16000:
                raise ValueError()
            payload = json.loads(self.rfile.read(length))
            if self.path == '/api/contract':
                self.reply(200, contract_case(payload.get('case_id')))
                return
            question = payload.get('question', '').strip()
            if not 1 <= len(question) <= 2500:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            self.reply(400, {'message': 'Nhập câu hỏi từ 1 đến 2500 ký tự.'})
            return
        if not RUN_LOCK.acquire(blocking=False):
            self.reply(409, {'message': 'Agent đang chạy, hãy chờ lượt hiện tại kết thúc.'})
            return
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True

            def emit(event):
                self.wfile.write((json.dumps(redact(event), ensure_ascii=False) + '\n').encode('utf-8'))
                self.wfile.flush()

            model = os.getenv('MODEL', '')
            provider = ObservedProvider(Provider(os.getenv('PROVIDER', 'openai'), model), emit)
            result = run_agent(question, provider, ObservedTools(emit), max_steps=6)
            report = redact({'event': 'done', 'kind': 'real', 'question': question,
                             'model': model, 'case_id': payload.get('case_id'),
                             'result': result, 'checks': provider.checks(result)})
            directory = ROOT / 'demo_runs'
            directory.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            (directory / (stamp + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            emit(report)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            try:
                emit({'event': 'error', 'message': 'Không chạy được agent. Kiểm tra cấu hình model/key hoặc kết nối trên máy chủ.'})
            except (BrokenPipeError, ConnectionResetError, UnboundLocalError):
                pass
        finally:
            RUN_LOCK.release()


if __name__ == '__main__':
    print('Demo CP2: http://127.0.0.1:8504', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8504), Handler).serve_forever()
