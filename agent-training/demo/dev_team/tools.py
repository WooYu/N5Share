"""Host tools: bounded context collection and a fixed, real test command."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

FIXTURES = Path(__file__).with_name('fixtures')
GUARD = "        if status not in STATUSES:\n            raise ValueError('不允许的任务状态')\n"


def prepare_workspace(root, scenario):
    root = Path(root)
    candidate = root / 'candidate'
    candidate.mkdir(parents=True, exist_ok=True)
    for name in ('board.py', 'index.html'):
        shutil.copyfile(FIXTURES / name, candidate / name)
    if scenario == 'buggy':
        source = (candidate / 'board.py').read_text(encoding='utf-8')
        (candidate / 'board.py').write_text(source.replace(GUARD, '        # 教学 PR：移除了状态校验\n'), encoding='utf-8')


def fingerprint(root):
    """Bind review, tests and approval to code AND trusted acceptance material."""
    from product_team.workspace import revision
    return revision(root)


def collect_context(root, incomplete=False, max_chars=24000):
    if (Path(root) / 'product.json').exists():
        from product_team.generation import product_context
        return product_context(root)
    current = (Path(root) / 'candidate' / 'board.py').read_text(encoding='utf-8')
    baseline = (FIXTURES / 'board.py').read_text(encoding='utf-8')
    files = {'board.py': current,
             'index.html': (Path(root) / 'candidate' / 'index.html').read_text(encoding='utf-8'),
             'test_board.py': (FIXTURES / 'test_board.py').read_text(encoding='utf-8')}
    if not incomplete:
        files['requirements.md'] = (FIXTURES / 'requirements.md').read_text(encoding='utf-8')
    truncated = []
    for name, source in list(files.items()):
        if len(source) > max_chars:
            files[name] = source[:max_chars]
            truncated.append(name)
    missing = [name for name in ('board.py', 'index.html', 'requirements.md', 'test_board.py') if name not in files]
    diff = ''.join(difflib.unified_diff(baseline.splitlines(True), current.splitlines(True),
                                       fromfile='base/board.py', tofile='head/board.py'))
    return {'revision': fingerprint(root), 'base_sha256': hashlib.sha256(baseline.encode()).hexdigest(),
            'head_sha256': hashlib.sha256(current.encode()).hexdigest(), 'diff': diff,
            'files': files, 'numbered_files': {name: '\n'.join(f'{i}: {line}' for i, line in enumerate(source.splitlines(), 1))
                                            for name, source in files.items()},
            'changed_files': ['board.py'] if baseline != current else [],
            'missing': missing, 'truncated': truncated, 'complete': not missing and not truncated}


def run_tests(root, timeout=120):
    """Never run a command proposed by the model; never accept model-written tests."""
    from product_team.acceptance import run_acceptance
    return run_acceptance(root, timeout)


def write_json(path, value):
    """Replace a state file atomically; JSON history alone is not framework recovery."""
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)
