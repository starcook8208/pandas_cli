"""Allow the original script entry points to run from an unpacked source checkout."""
from pathlib import Path
import sys

source = Path(__file__).resolve().parents[1] / "src"
if str(source) not in sys.path:
    sys.path.insert(0, str(source))
