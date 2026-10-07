"""Allow unittest discovery and direct tests after separating source and tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / 'course', ROOT / 'demo/reference', ROOT / 'demo'):
    sys.path.insert(0, str(folder))
