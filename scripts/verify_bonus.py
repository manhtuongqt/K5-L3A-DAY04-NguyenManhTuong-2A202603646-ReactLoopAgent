"""Lưu tests, hash phiên bản bonus và kiểm tra tương thích core offline."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def run_suite(folder, output):
    with output.open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.TestLoader().discover(str(ROOT / folder)))
    return {'total': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors),
            'failures': len(result.failures), 'errors': len(result.errors)}


def main():
    out = ROOT / 'artifacts/bonus'
    out.mkdir(parents=True, exist_ok=True)
    tests = run_suite('tests', out / 'unit_tests.txt')
    # Use a separate loader to avoid test module-name collisions.
    bonus = run_suite('bonus', out / 'bonus_tests.txt')
    snapshot = json.loads((ROOT / 'artifacts/cp5_improved/manifest.json').read_text(encoding='utf-8'))
    core_intact = all(sha('artifacts/cp5_improved/'+p) == value for p, value in snapshot['files'].items())
    for path in ['agent.py', 'providers.py', 'bonus/runtime.py']:
        dest = out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / path).read_bytes())
    protected = ['bonus/tools.py', 'bonus/cases.json'] + [str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'bonus/fixtures').glob('*.json')]
    proof = {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'main_tests': tests, 'bonus_tests': bonus,
        'current_agent_sha256': sha('agent.py'), 'bonus_runtime_sha256': sha('bonus/runtime.py'),
        'core_snapshot_sha256': snapshot['files']['agent.py'], 'core_snapshot_intact': core_intact,
        'core_contract_parity': tests['failures'] == tests['errors'] == 0,
        'core_contract_parity_scope': 'Six scripted core trajectories compare result and provider messages with evaluated CP5 snapshot. Not a new core API eval.',
        'protected_bonus_sha256': {p: sha(p) for p in protected},
    }
    (out / 'verification.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'tests': tests, 'bonus_tests': bonus, 'core_snapshot_intact': core_intact}))
    return 0 if tests['failures'] == tests['errors'] == bonus['failures'] == bonus['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
