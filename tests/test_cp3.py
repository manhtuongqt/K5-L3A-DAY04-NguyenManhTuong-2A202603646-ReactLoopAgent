"""Các nhánh lỗi CP3 bổ sung; không gọi mạng hay sửa tests của đề."""
import json
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class RobustnessTests(unittest.TestCase):
    def test_provider_exception_stops_without_disclosing_message(self):
        class BrokenProvider:
            def complete(self, messages, schemas):
                raise RuntimeError('private-test-credential')

        result = run_agent('check', BrokenProvider(), StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][0]['event'], 'provider_error')
        self.assertNotIn('private-test-credential', json.dumps(result))

    def test_tool_exception_is_observation_and_model_can_continue(self):
        class BrokenTools:
            def execute(self, name, args):
                raise TimeoutError('private-error-detail')

        fake = FakeProvider([
            tool_call('timeout-1', 'get_status', '{"provider":"github"}'),
            final('Không lấy được dữ liệu, chưa thể kết luận trạng thái.'),
        ])
        result = run_agent('check', fake, BrokenTools())
        observation = fake.histories[1][-1]
        self.assertEqual(observation['tool_call_id'], 'timeout-1')
        self.assertEqual(json.loads(observation['content'])['error'], 'TimeoutError')
        self.assertEqual(result['status'], 'completed')
        self.assertNotIn('private-error-detail', json.dumps(result))

    def test_non_object_json_is_rejected_before_execution(self):
        for arguments in ['[]', 'null', '1', '"text"']:
            with self.subTest(arguments=arguments):
                fake = FakeProvider([tool_call('bad', 'get_status', arguments), final()])
                run_agent('check', fake, StatusTools())
                self.assertEqual(json.loads(fake.histories[1][-1]['content'])['error'],
                                 'INVALID_ARGUMENTS')

    def test_partial_tool_failure_still_returns_every_call_id(self):
        response = tool_call('bad', 'get_status', '{')
        good = tool_call('good', 'get_status', '{"provider":"github"}')
        response['calls'].extend(good['calls'])
        response['message']['tool_calls'].extend(good['message']['tool_calls'])
        fake = FakeProvider([response, final()])
        run_agent('check', fake, StatusTools())
        observations = fake.histories[1][-2:]
        self.assertEqual([m['tool_call_id'] for m in observations], ['bad', 'good'])
        self.assertEqual(json.loads(observations[0]['content'])['error'], 'INVALID_ARGUMENTS')
        self.assertEqual(json.loads(observations[1]['content'])['provider'], 'github')

    def test_unexpected_finish_is_not_completed_and_does_not_execute(self):
        for finish in ['length', 'content_filter', None]:
            with self.subTest(finish=finish):
                response = tool_call('cut', 'get_status', '{"provider":"github"}')
                response['finish'] = finish
                result = run_agent('check', FakeProvider([response]), StatusTools())
                self.assertEqual(result['status'], 'error')
                self.assertFalse(any(e['event'] == 'tool' for e in result['trace']))
                self.assertEqual(result['trace'][-1]['event'], 'error')

    def test_invalid_budget_does_not_call_provider(self):
        for budget in [0, -1, True, 1.5]:
            with self.subTest(budget=budget):
                fake = FakeProvider([])
                result = run_agent('check', fake, StatusTools(), max_steps=budget)
                self.assertEqual(result['status'], 'error')
                self.assertEqual(fake.histories, [])


if __name__ == '__main__':
    unittest.main()
