"""Rebuild a clean source-only copy using the same Git file policy."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
from check_git_files import ROOT, allowed, git


def main():
    names = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', '.').decode('utf-8').split('\0'))
    with tempfile.TemporaryDirectory(prefix='agent-training-source-') as directory:
        checkout = Path(directory).resolve()
        count = 0
        for name in sorted(names):
            source = ROOT / name
            if not name or not source.is_file() or not allowed(Path(name)):
                continue
            if not source.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('Source path escaped the project: ' + name)
            target = checkout / name
            if not target.resolve().is_relative_to(checkout):
                raise ValueError('Target path escaped the temporary checkout')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            count += 1
        assert not (checkout / 'index.html').exists()
        for args in (['build.py'], ['demo/run_collaboration.py', '--help']):
            result = subprocess.run([sys.executable, *args], cwd=checkout,
                                    capture_output=True, text=True, encoding='utf-8', timeout=60,
                                    env={**os.environ, 'PYTHONUTF8': '1'})
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
        for name in ('index.html', 'docs/outline.md', 'docs/speaker-notes.md',
                     'demo/fixtures.json', 'archive/2026-10-07-before-collaboration-import/slides.json'):
            assert (checkout / name).is_file(), name
        print(f'Source-only checkout verified: {count} files; presentation rebuilt and live CLI entry available.')


if __name__ == '__main__':
    main()
