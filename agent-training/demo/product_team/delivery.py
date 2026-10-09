"""Version-bound approval, release checks and container-only serving."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import zipfile
import subprocess

from .acceptance import run_acceptance
from .sandbox import Sandbox, SandboxError
from .workspace import digest, material, read_sources, revision, snapshot


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


@contextmanager
def run_lock(root):
    """OS releases the lock on crash; stale lock files do not block recovery."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.run.lock').open('a+b') as stream:
        stream.seek(0)
        stream.write(b'0')
        stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError('This run is already in use by another process') from None
        try:
            yield root
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def evidence_digest(state):
    return hashlib.sha256(json.dumps({'review': state['review'], 'tests': state['tests']},
                                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def current_actor():
    if os.name == 'nt':
        return subprocess.check_output([str(Path(os.environ['SystemRoot']) / 'System32/whoami.exe')],
                                       text=True, timeout=5).strip()
    import pwd
    return pwd.getpwuid(os.getuid()).pw_name


def approve(root, decision, version):
    root = Path(root).resolve()
    with run_lock(root):
        state = json.loads((root / 'state.json').read_text(encoding='utf-8'))
        if state.get('status') != 'waiting_approval' or version != revision(root):
            raise ValueError('没有待审批的当前版本；请重新评审与验收')
        if decision not in ('approve', 'reject'):
            raise ValueError('Unknown decision')
        now = datetime.now(timezone.utc)
        approval = {'decision': decision, 'revision': version, 'actor': current_actor(),
                    'at': now.isoformat(), 'expires': (now + timedelta(hours=24)).isoformat()}
        if decision == 'reject':
            state.setdefault('decisions', []).append(approval)
            state.update(status='rejected', human_decision=approval)
            write_json(root / 'state.json', state)
            return state
        from .gates import delivery_gate
        tests = run_acceptance(root)
        state['tests'] = tests
        gate = delivery_gate(root, state.get('review', {}), tests, 'approve', version)
        if gate['status'] != 'completed':
            state.update(gate)
            write_json(root / 'state.json', state)
            return state
        release_version, release = snapshot(root)
        if release_version != version:
            raise ValueError('审批过程中源码变化')
        approval.update(evidence_sha256=evidence_digest(state), image=tests['image'])
        state.setdefault('decisions', []).append(approval)
        state.update(status='completed', human_decision=approval, release=version)
        write_json(root / 'approval.json', approval)
        write_json(release / 'approval.json', approval)
        write_json(root / 'state.json', state)
        export_release(root)
        return state


def approved_release(root):
    root = Path(root).resolve()
    state = json.loads((root / 'state.json').read_text(encoding='utf-8'))
    approval = json.loads((root / 'approval.json').read_text(encoding='utf-8'))
    version = revision(root)
    if state.get('status') != 'completed' or approval.get('decision') != 'approve' or not approval.get('actor'):
        raise ValueError('正式启动需要当前版本人工批准')
    if state.get('human_decision') != approval or state.get('release') != version or approval.get('revision') != version:
        raise ValueError('批准已过期：源码、需求或批准记录变化')
    if datetime.fromisoformat(approval['expires']) <= datetime.now(timezone.utc):
        raise ValueError('批准已超过有效期，请重新评审并批准')
    tests, review = state.get('tests', {}), state.get('review', {})
    from .gates import delivery_gate
    if (delivery_gate(root, review, tests, 'approve', version)['status'] != 'completed'
            or tests.get('image') != approval.get('image')
            or evidence_digest(state) != approval.get('evidence_sha256')):
        raise ValueError('评审或真实验收证据无效')
    release = root / 'releases' / version
    if json.loads((release / 'approval.json').read_text(encoding='utf-8')) != approval:
        raise ValueError('交付快照批准记录不一致')
    if digest(read_sources(release / 'candidate'), json.loads((release / 'product.json').read_text(encoding='utf-8'))) != version:
        raise ValueError('已批准交付快照被修改')
    return release, approval


def proxy_handler(box):
    class Handler(BaseHTTPRequestHandler):
        def dispatch(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 65536:
                    raise ValueError('Request too large')
                body = json.loads(self.rfile.read(size)) if size else None
                headers = {k: self.headers[k] for k in ('Authorization', 'Idempotency-Key', 'Content-Type') if k in self.headers}
                response = box.request(self.path, self.command, body, headers)
                self.send_response(response['status'])
                self.send_header('Content-Type', response['content_type'])
                self.send_header('Content-Length', str(len(response['raw'])))
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(response['raw'])
            except (ValueError, SandboxError):
                self.send_error(502, 'Application request failed')
        do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = dispatch

        def log_message(self, *_):
            pass
    return Handler


def serve(root, port=8766):
    root = Path(root).resolve()
    with run_lock(root):
        release, approval = approved_release(root)
        with Sandbox(release / 'candidate', approval['image'], legacy=bool(material(root).get('legacy')),
                     data=root / 'data', expected_revision=approval['revision'], contract=material(root)) as box:
            with ThreadingHTTPServer(('127.0.0.1', port), proxy_handler(box)) as server:
                print(f"Approved {approval['revision']} at http://127.0.0.1:{server.server_port}", flush=True)
                server.serve_forever()


def export_release(root):
    root = Path(root)
    release, approval = approved_release(root)
    target = root / ('delivery-' + approval['revision'][:12] + '.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in release.rglob('*'):
            if path.is_file():
                archive.write(path, 'releases/' + release.name + '/' + path.relative_to(release).as_posix())
        for path in (root / 'candidate').rglob('*'):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
        for name in ('state.json', 'approval.json'):
            archive.write(root / name, name)
        archive.write(release / 'product.json', 'product.json')
        for name in ('requirements-generated.md', 'design-generated.md'):
            if (root / name).exists():
                archive.write(root / name, name)
        for path in Path(__file__).parent.rglob('*.py'):
            archive.write(path, 'product_team/' + path.relative_to(Path(__file__).parent).as_posix())
        archive.writestr('serve.py', "from pathlib import Path\nfrom product_team.delivery import serve\nserve(Path(__file__).parent)\n")
        archive.writestr('DELIVERY.md', f"# Approved application\n\nRun `python serve.py` with Docker Linux running. Load the exact runtime image {approval['image']} first (docker save / docker load). No pip dependencies.\n\nOnly data/ is writable; back up data/ before upgrades. Stop the service before switching to a separately approved release; restore that release's database backup when rolling back. Approval expires at {approval['expires']}. Local OS-user approval, not enterprise identity authentication.\n")
    return target
