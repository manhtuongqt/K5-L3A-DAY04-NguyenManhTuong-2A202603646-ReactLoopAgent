"""Kiểm tra retry/context bonus và tương thích với bản CP5 đã được eval."""
import copy
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from agent import run_agent
from bonus.runtime import retry_seconds
from bonus.tools import BonusTools
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class BonusExtensionTests(unittest.TestCase):
    def test_core_trajectories_match_evaluated_cp5_snapshot(self):
        path = Path(__file__).resolve().parents[1] / 'artifacts/cp5_improved/agent.py'
        spec = importlib.util.spec_from_file_location('evaluated_cp5', path)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        multi = tool_call('a', 'get_status', '{"provider":"github"}')
        other = tool_call('b', 'get_status', '{"provider":"cloudflare"}')
        multi['calls'] += other['calls']
        multi['message']['tool_calls'] += other['message']['tool_calls']
        url = StatusTools().get_incident_details('github', 'xr3myzj7ms51')['url']
        scenarios = [
            [final()],
            [tool_call('s', 'get_status', '{"provider":"github"}'), final()],
            [multi, final()],
            [tool_call('j', 'get_status', '{'), final()],
            [{**final('cut'), 'finish': 'length'}],
            [tool_call('i', 'get_incident_details', '{"provider":"github","incident_id":"xr3myzj7ms51"}'), final('missing'), final(url)],
        ]
        for responses in scenarios:
            with self.subTest(responses=responses):
                old, new = FakeProvider(copy.deepcopy(responses)), FakeProvider(copy.deepcopy(responses))
                expected = baseline.run_agent('check', old, StatusTools())
                actual = run_agent('check', new, StatusTools())
                self.assertEqual(actual, expected)
                self.assertEqual(new.histories, old.histories)

    def test_persistent_429_stops_actual_tool_calls_at_three(self):
        tools = BonusTools(scenario='rate_limit_always')
        responses = [tool_call(str(i), 'get_vercel_status', '{}') for i in range(5)] + [final('Unknown due to rate limit.')]
        fake = FakeProvider(responses)
        result = run_agent('check', fake, tools, max_steps=8)
        self.assertEqual(tools.calls[('get_vercel_status', 'vercel')], 3)
        self.assertEqual(sum(e['event'] == 'tool' for e in result['trace']), 3)
        self.assertEqual(sum(e['event'] == 'retry_blocked' for e in result['trace']), 2)
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(json.loads(fake.histories[-1][-1]['content'])['retry_allowed'])

    def test_long_retry_after_blocks_without_early_request(self):
        class LongWait(BonusTools):
            def execute(self, name, args):
                self.count = getattr(self, 'count', 0)+1
                return {'ok': False, 'error': 'RATE_LIMITED', 'http_status': 429, 'retry_after': '3600'}
        tools = LongWait()
        fake = FakeProvider([tool_call('1', 'get_vercel_status', '{}'), tool_call('2', 'get_vercel_status', '{}'), final()])
        with patch('bonus.runtime.time.sleep') as sleep:
            result = run_agent('check', fake, tools)
            sleep.assert_not_called()
        self.assertEqual(tools.count, 1)
        self.assertEqual(result['trace'][-2]['event'], 'retry_blocked')

    def test_short_retry_after_waits_before_request(self):
        class ShortWait(BonusTools):
            def execute(self, name, args):
                self.count = getattr(self, 'count', 0)+1
                return ({'error': 'RATE_LIMITED', 'retry_after': '1'} if self.count == 1 else {'provider': 'vercel'})
        tools = ShortWait()
        fake = FakeProvider([tool_call('1', 'get_vercel_status', '{}'), tool_call('2', 'get_vercel_status', '{}'), final()])
        with patch('bonus.runtime.time.monotonic', return_value=10.0), patch('bonus.runtime.time.sleep') as sleep:
            run_agent('check', fake, tools)
            sleep.assert_called_once_with(1.0)
        self.assertEqual(tools.count, 2)

    def test_http_date_retry_after_is_supported(self):
        future = datetime.now(timezone.utc)+timedelta(seconds=60)
        delay = retry_seconds({'retry_after': format_datetime(future, usegmt=True)})
        self.assertTrue(30 <= delay <= 61)

    def test_noise_removed_only_from_model_context_not_trace(self):
        tools = BonusTools(scenario='noisy')
        fake = FakeProvider([tool_call('1', 'get_vercel_status', '{}'), final()])
        result = run_agent('check', fake, tools)
        native_result = json.loads(fake.histories[1][-1]['content'])
        self.assertNotIn('distractors', native_result)
        self.assertIn('160', native_result['context_note'])
        raw = next(e['result'] for e in result['trace'] if e['event'] == 'tool')
        self.assertEqual(len(raw['distractors']), 160)
        self.assertTrue(any(e['event'] == 'context_compacted' for e in result['trace']))
