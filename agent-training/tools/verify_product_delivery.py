"""Revalidate an approved delivery in a fresh directory; no model or approval action."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def verify(archive, output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='clean-product-delivery-') as directory:
        target = Path(directory)
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                resolved = (target / entry.filename).resolve()
                if not resolved.is_relative_to(target) or entry.file_size > 8_000_000:
                    raise ValueError('Unsafe delivery archive')
            bundle.extractall(target)
        # Run the exported verifier in a new interpreter with only the extracted bundle.
        script = (
            "import json,sys\nfrom pathlib import Path\n"
            "from product_team.delivery import approved_release\n"
            "from product_team.acceptance import run_acceptance\n"
            "root=Path.cwd()\nrelease,approval=approved_release(root)\n"
            "import threading\nfrom urllib.request import urlopen\n"
            "from http.server import ThreadingHTTPServer\nfrom product_team import delivery\n"
            "startup=[]\n"
            "class OneRequestServer(ThreadingHTTPServer):\n"
            "    def serve_forever(self):\n"
            "        def client():\n"
            "            try:\n"
            "                with urlopen('http://127.0.0.1:'+str(self.server_port)+'/',timeout=30) as response:\n"
            "                    startup.append(response.status==200 and bool(response.read()))\n"
            "            except Exception:\n"
            "                startup.append(False)\n"
            "        thread=threading.Thread(target=client,daemon=True)\n"
            "        thread.start()\n        self.timeout=35\n        self.handle_request()\n        thread.join(35)\n"
            "delivery.ThreadingHTTPServer=OneRequestServer\ndelivery.serve(root,0)\n"
            "result=run_acceptance(root,300)\n"
            "result['formal_startup_passed']=startup==[True]\n"
            "result['passed']=result['passed'] and result['formal_startup_passed']\n"
            "Path(sys.argv[1]).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')\n"
            "raise SystemExit(0 if result['passed'] else 2)\n"
        )
        (target / 'verify.py').write_text(script, encoding='utf-8')
        result = subprocess.run([sys.executable, '-E', '-B', 'verify.py', str(output)], cwd=target, timeout=420)
        # Screenshots are evidence, so keep them after the clean directory is removed.
        import shutil
        screenshots = list(target.glob('releases/*/browser-evidence/*.png'))
        destination = output.parent / (output.stem + '-screenshots')
        if screenshots:
            destination.mkdir(exist_ok=True)
            for path in screenshots:
                shutil.copyfile(path, destination / path.name)
        return result.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(verify(args.archive, args.output))
