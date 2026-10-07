"""Check candidate Git files without reading provider credentials or modifying Git."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = {'course', 'web', 'demo', 'docs', 'tests', 'tools', 'assets', 'config'}
ROOT_FILES = {'.gitignore', '.gitattributes', 'README.md', 'build.py',
              'requirements.txt', 'start-demo.cmd', 'start-collaboration.cmd'}
VSCODE_FILES = {'launch.json', 'extensions.json', 'settings.json'}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def allowed(path):
    parts = path.parts
    if path.name == '.env.example':
        return parts[0] == 'config'
    if (any(part in {'__pycache__', '.venv', 'venv', '.langgraph_api', 'node_modules',
                     'output', 'test-results', 'dist', 'work-notes', 'generated-examples',
                     'sample-output', 'collaboration-sample-output'} for part in parts)
            or path.name.startswith('.env') or path.suffix in {'.key', '.pem', '.dpapi', '.zip'}):
        return False
    if path.as_posix() in {'index.html', 'outline.md', 'speaker-notes.md',
                           'docs/outline.md', 'docs/speaker-notes.md', 'deepseek.config'}:
        return False
    if len(parts) == 1:
        return path.name in ROOT_FILES
    if parts[0] == '.vscode':
        return len(parts) == 2 and parts[1] in VSCODE_FILES
    if parts[0] == 'archive':
        return (parts[1] == '2026-10-07-before-collaboration-import'
                or path.as_posix() == 'archive/2026-10-08-directory-organization.json')
    if parts[0] == 'config':
        return False
    return parts[0] in SOURCE_DIRS


def main():
    candidates = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', '.').decode('utf-8').split('\0'))
    invalid, count = [], 0
    for name in sorted(candidates):
        if not name or not (ROOT / name).is_file():
            continue
        count += 1
        if not allowed(Path(name)):
            invalid.append(name)
    # Ignored tracked paths can remain in the index even after the local file moved.
    tracked_ignored = git('ls-files', '--cached', '--ignored', '--exclude-standard', '-z', '--', '.').decode('utf-8').split('\0')
    invalid = sorted(set(invalid) | {name for name in tracked_ignored if name})
    if invalid:
        raise SystemExit('Files outside the commit policy:\n' + '\n'.join(invalid))
    print(f'Git file policy passed: {count} source, documentation and reference files; no tracked ignored files.')


if __name__ == '__main__':
    main()
