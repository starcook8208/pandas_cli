"""Workspace launcher that preserves the caller's working directory and arguments."""
from pathlib import Path
import sys

# Explicit source path also works in isolated (-I) Python mode.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pandas_processor.entry import main

if __name__ == "__main__":
    raise SystemExit(main())
