"""Nạp .env cục bộ rồi chạy script Python, không thực thi nội dung file env."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print('Usage: python with_env.py run.py "Câu hỏi"', file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent
    env = dict(os.environ)
    path = root / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line.startswith('export '):
                line = line[7:]
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            env[key.strip()] = value.strip().strip('\"\'')
    env['PYTHONIOENCODING'] = 'utf-8'
    return subprocess.call([sys.executable, *sys.argv[1:]], cwd=root, env=env)


if __name__ == '__main__':
    sys.exit(main())
