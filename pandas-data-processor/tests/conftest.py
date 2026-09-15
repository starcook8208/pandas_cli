"""Shared fixtures and subprocess CLI runner."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture
def fixtures() -> Path:
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def schema() -> dict:
    return json.loads((ROOT / "specs" / "schema.example.json").read_text(encoding="utf-8"))


@pytest.fixture
def contract(fixtures: Path) -> dict:
    return json.loads((fixtures / "result.json").read_text(encoding="utf-8"))


@pytest.fixture
def cli():
    def run(name, *args, expected=0):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{name}.py"), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8", timeout=45)
        assert result.returncode == expected, (result.stdout, result.stderr)
        assert not result.stderr, result.stderr
        return json.loads(result.stdout)
    return run
