"""Package complete live-model examples; use an explicit file allowlist."""
from pathlib import Path
import json
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    '.gitignore': '.gitignore',
    '.gitattributes': '.gitattributes',
    'config/.env.example': 'config/.env.example',
    'docs/collaboration-demo-guide.md': 'README.md',
    'start-collaboration.cmd': 'start-collaboration.cmd',
    'requirements.txt': 'requirements.txt',
    '.vscode/launch.json': '.vscode/launch.json',
    '.vscode/extensions.json': '.vscode/extensions.json',
    '.vscode/settings.json': '.vscode/settings.json',
}
for name in ('run_collaboration.py', 'model_gateway.py', 'model_backup.py',
             'secret_store.py', 'process_scope.py'):
    FILES['demo/' + name] = 'demo/' + name
for name in ('__init__.py', 'state.py', 'tools.py', 'agents.py', 'runtime.py', 'console.py',
             'sequential.py', 'supervisor.py', 'hierarchical.py', 'swarm.py', 'network.py'):
    FILES['demo/collaboration_live/' + name] = 'demo/collaboration_live/' + name
for name in ('_bootstrap.py', 'test_collaboration_live.py'):
    FILES['tests/' + name] = 'tests/' + name


def main():
    destination = ROOT / 'dist/collaboration-demo.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for source, target in FILES.items():
            data = (ROOT / source).read_bytes()
            if target == 'README.md':
                data = data.decode('utf-8').replace('](../', '](').encode('utf-8')
            if target == '.vscode/launch.json':
                config = json.loads(data)
                config['configurations'] = [item for item in config['configurations']
                    if item['program'] == '${workspaceFolder}/demo/run_collaboration.py']
                config['inputs'] = [item for item in config['inputs'] if item['id'] == 'scenario']
                data = json.dumps(config, ensure_ascii=False, indent=2).encode('utf-8')
            if target.endswith('.cmd'):
                data = data.decode('utf-8').replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
            archive.writestr('collaboration-demo/' + target, data)
    print(str(destination))


if __name__ == '__main__':
    main()
