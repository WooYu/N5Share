"""Both lecture frontends use the same executable product pipeline and gates."""
from pathlib import Path
import os
import subprocess


ROOT = Path(__file__).resolve().parents[2] / 'agent-training'


def command():
    configured = os.environ.get('TRAINING_PRODUCT_PYTHON')
    python = Path(configured) if configured else ROOT / '.venv-metagpt' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        raise ValueError('Prepare agent-training/.venv-metagpt or set TRAINING_PRODUCT_PYTHON')
    return [str(python), '-X', 'utf8', str(ROOT / 'demo/run_dev_team.py')]


def run(args):
    if args.approve:
        raise ValueError('--approve cannot approve future output; use --decision approve --run-dir PATH --revision SHA')
    argv = []
    for name in ('requirements', 'output', 'decision', 'run_dir', 'revision'):
        value = getattr(args, name, None)
        if value:
            if name in ('requirements', 'output', 'run_dir'):
                value = Path(value).resolve()
            argv.extend(['--' + name.replace('_', '-'), str(value)])
    for name in ('check', 'resume'):
        if getattr(args, name, False):
            argv.append('--' + name)
    if not (args.check or args.decision or args.resume or args.requirements):
        raise ValueError('Product development requires --requirements JSON; free text alone has no verifiable acceptance')
    return subprocess.call(command() + argv, cwd=ROOT)
