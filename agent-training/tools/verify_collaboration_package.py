"""Exercise delivered live graphs with external model fixtures, without API cost."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='collaboration 中文 空格 ') as directory:
        with ZipFile(ROOT / 'dist/collaboration-demo.zip') as archive:
            names = archive.namelist()
            required = ['README.md', 'requirements.txt', 'start-collaboration.cmd',
                        '.gitignore', '.gitattributes', 'config/.env.example',
                        '.vscode/launch.json', 'demo/run_collaboration.py',
                        'demo/model_backup.py', 'demo/collaboration_live/console.py',
                        'tests/_bootstrap.py', 'tests/test_collaboration_live.py']
            required += ['demo/collaboration_live/' + name + '.py' for name in
                         ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network')]
            assert all('collaboration-demo/' + name in names for name in required)
            assert not any(part in name for name in names for part in
                           ('/.venv/', '/output/', '.dpapi', 'collaboration_patterns.py'))
            assert not any(Path(name).name.startswith('.env') and Path(name).name != '.env.example' for name in names)
            archive.extractall(directory)
        demo_root = Path(directory) / 'collaboration-demo'
        env = dict(os.environ, PYTHONUTF8='1')
        env.pop('PYTHONPATH', None)

        def execute(arguments, cwd=demo_root):
            result = subprocess.run([sys.executable, *arguments], cwd=cwd, env=env,
                                    capture_output=True, text=True, encoding='utf-8', timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
            return result

        tests = execute(['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_collaboration_live.py'])
        print(tests.stderr.strip())
        execute(['demo/run_collaboration.py', '--help'])
        for pattern in ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network'):
            execute(['-m', 'collaboration_live.' + pattern, '--help'], cwd=demo_root / 'demo')
        configs = json.loads((demo_root / '.vscode/launch.json').read_text(encoding='utf-8'))
        for config in configs['configurations']:
            assert config['program'] == '${workspaceFolder}/demo/run_collaboration.py'
            assert config['console'] == 'integratedTerminal'
            assert config['python'] == '${workspaceFolder}/.venv/Scripts/python.exe'
        if os.name == 'nt':
            # Validate the missing-setup branch in the clean extracted package.
            result = subprocess.run(['cmd.exe', '/d', '/c', 'start-collaboration.cmd', '--check-model'],
                                    cwd=demo_root, env=env, capture_output=True, timeout=30)
            assert result.returncode == 1
            assert b'pip install -r requirements.txt' in result.stdout
        print('Live-example ZIP verified in an extracted path with spaces and Chinese characters.')


if __name__ == '__main__':
    main()
