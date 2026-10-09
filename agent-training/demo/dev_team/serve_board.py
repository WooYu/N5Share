"""Start only an approved snapshot in Docker; expose a loopback HTTP proxy."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from product_team.delivery import serve

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    try:
        serve(args.run_dir, args.port)
    except (ValueError, OSError, KeyError, RuntimeError) as error:
        parser.exit(2, 'Start refused: ' + str(error) + '\n')
