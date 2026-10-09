"""Bounded model file bundles and immutable content-addressed snapshots."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

ALLOWED = {'.py', '.html', '.css', '.js', '.json', '.md', '.sql', '.txt', '.lock'}
REQUIRED = {'app.py', 'README.md', 'requirements.lock'}


def safe_name(name):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_./-]{1,120}', name):
        raise ValueError('Invalid source path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or name != path.as_posix() or any(p.startswith('.') for p in path.parts):
        raise ValueError('Source path escapes the workspace')
    if path.suffix not in ALLOWED or any(p.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))} for p in path.parts):
        raise ValueError('Unsupported source file')
    return name


def read_sources(folder):
    folder = Path(folder)
    if folder.is_symlink() or (hasattr(folder, 'is_junction') and folder.is_junction()):
        raise ValueError('Linked source directory is forbidden')
    files = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Linked source files are forbidden')
        if path.is_file():
            name = safe_name(path.relative_to(folder).as_posix())
            if path.stat().st_size > 150000:
                raise ValueError('Source file is too large')
            files[name] = path.read_text(encoding='utf-8')
    if not files or len(files) > 40 or sum(len(s.encode()) for s in files.values()) > 500000:
        raise ValueError('Empty or oversized source bundle')
    if len({n.lower() for n in files}) != len(files):
        raise ValueError('Case-colliding source paths')
    return files


def validate_bundle(value):
    if not isinstance(value, dict) or set(value) != {'files', 'summary'} or not isinstance(value['summary'], str):
        raise ValueError('Expected files and summary')
    files = value['files']
    if not isinstance(files, list) or not 5 <= len(files) <= 40:
        raise ValueError('Provide a complete multi-file application')
    result = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {'path', 'content'}:
            raise ValueError('Invalid source entry')
        name = safe_name(item['path'])
        content = item['content']
        if name.lower() in {p.lower() for p in result} or not isinstance(content, str) or len(content) > 150000:
            raise ValueError('Duplicate or oversized source')
        if name.endswith('.py'):
            compile(content, name, 'exec')  # Syntax inspection only; never execute.
        result[name] = content
    missing = sorted(REQUIRED - result.keys())
    if missing:
        raise ValueError('Missing required root files: ' + ', '.join(missing) + '; received: ' + ', '.join(result))
    if not any(n.endswith('.html') for n in result) or len([n for n in result if n.endswith('.py')]) < 2:
        raise ValueError('Need an HTML frontend (may be nested) and at least two Python modules; received: ' + ', '.join(result))
    if any(line.strip() and not line.lstrip().startswith('#') for line in result['requirements.lock'].splitlines()):
        raise ValueError('This runtime supports the Python standard library only')
    if sum(len(s.encode()) for s in result.values()) > 500000:
        raise ValueError('Source bundle exceeds budget')
    return value


def write_bundle(root, value):
    validate_bundle(value)
    root = Path(root)
    # Validate the entire response before replacing any files. Include deletions.
    with tempfile.TemporaryDirectory(dir=root, prefix='source-stage-') as directory:
        stage = Path(directory) / 'candidate'
        stage.mkdir()
        for item in value['files']:
            path = stage / item['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(item['content'], encoding='utf-8')
        read_sources(stage)
        candidate = root / 'candidate'
        if candidate.exists():
            read_sources(candidate)
            candidate.rename(Path(directory) / 'previous')
        try:
            stage.rename(candidate)
        except OSError:
            previous = Path(directory) / 'previous'
            if previous.exists() and not candidate.exists():
                previous.rename(candidate)
            raise


def digest(files, material):
    policy = Path(__file__).parent
    trusted = {p.relative_to(policy).as_posix(): p.read_text(encoding='utf-8-sig')
               for p in sorted(policy.rglob('*.py')) if '__pycache__' not in p.parts}
    return hashlib.sha256(json.dumps({'files': files, 'material': material, 'verifier': trusted}, ensure_ascii=False,
                                    sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def material(root):
    path = Path(root) / 'product.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    from dev_team.tools import FIXTURES
    return {'legacy': True, 'requirements': (FIXTURES / 'requirements.md').read_text(encoding='utf-8')}


def revision(root):
    return digest(read_sources(Path(root) / 'candidate'), material(root))


def snapshot(root):
    root = Path(root)
    files, contract = read_sources(root / 'candidate'), material(root)
    version = digest(files, contract)
    destination = root / 'releases' / version
    if destination.exists():
        if digest(read_sources(destination / 'candidate'), json.loads((destination / 'product.json').read_text(encoding='utf-8'))) != version:
            raise ValueError('Existing release has been modified')
        return version, destination
    destination.mkdir(parents=True)
    (destination / 'candidate').mkdir()
    for name, content in files.items():
        path = destination / 'candidate' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    (destination / 'product.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding='utf-8')
    return version, destination
