"""Kiểm tra demo không gắn nhãn sai dữ liệu hoặc làm đổi loop."""
import unittest

from lab_demo import contract_case, evidence


class DemoEvidenceTests(unittest.TestCase):
    def test_offline_cases_are_explicitly_labelled_and_use_real_loop(self):
        expected = {'invalid_json': 'completed', 'timeout': 'completed',
                    'length': 'error', 'max_steps': 'max_steps', 'missing_source': 'completed'}
        for name, status in expected.items():
            with self.subTest(case=name):
                report = contract_case(name)
                self.assertEqual(report['kind'], 'contract')
                self.assertEqual(report['model'], 'FakeProvider (offline)')
                self.assertEqual(report['result']['status'], status)
                self.assertIsNone(report['checks']['tool_results_linked'])

    def test_missing_source_really_triggers_revision(self):
        result = contract_case('missing_source')['result']
        self.assertTrue(any(e['event'] == 'validation_missing_source' for e in result['trace']))
        self.assertEqual(len(result['usage']), 3)
        self.assertIn('https://', result['answer'])

    def test_saved_h3_keeps_actual_failure_instead_of_fabricating_pass(self):
        report = evidence('before', 'H3')
        self.assertEqual(report['kind'], 'saved')
        tools = [e['name'] for e in report['result']['trace'] if e['event'] == 'tool']
        self.assertNotIn('get_incident_details', tools)
        self.assertIsNone(report['checks']['all_calls_returned'])

    def test_evidence_rejects_arbitrary_phase_or_unknown_case(self):
        for phase, case_id in [('../.env', 'H3'), ('before', 'unknown')]:
            with self.subTest(phase=phase):
                with self.assertRaises(ValueError):
                    evidence(phase, case_id)
