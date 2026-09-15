"""Run real macOS installation and CLI checks, retaining evidence for review.

Usage on a Mac with Python 3.11+: python3 scripts/verify_macos.py
Creates a separate test environment; never reuses or replaces the user's .venv.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import venv
import xml.etree.ElementTree as ET


def main() -> int:
    argparse.ArgumentParser(
        description="On a real Mac, install a fresh test environment and save pytest/CLI evidence.",
        epilog="Requires Python 3.11+ and network access for dependencies. Results: .macos-test-runs/",
    ).parse_args()
    if sys.platform != "darwin" or platform.system() != "Darwin":
        print(json.dumps({"status": "error", "error": {
            "code": "MACOS_REQUIRED",
            "message": "Run this verifier on a real Mac. Other platforms cannot establish macOS compatibility.",
        }, "detected_platform": sys.platform}))
        return 3
    if sys.version_info < (3, 11):
        print(json.dumps({"status": "error", "error": {
            "code": "PYTHON_VERSION", "message": "Python 3.11 or newer is required.",
        }, "python_version": platform.python_version()}))
        return 3

    root = Path(__file__).resolve().parents[1]
    results_root = root / ".macos-test-runs"
    results_root.mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=results_root))
    report_path = run / "report.json"
    report = {
        "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
        "system": platform.system(), "macos_version": platform.mac_ver()[0],
        "process_architecture": platform.machine(), "bootstrap_python": sys.executable,
        "python_version": platform.python_version(), "steps": [],
        "scope": "Fresh installation, existing pytest suite, and small CSV/XLSX CLI workflows; not a capacity benchmark.",
    }

    def save() -> None:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def step(name: str, args: list[str | Path], *, cwd: Path, expected: int = 0,
             timeout: int = 600) -> Path:
        log = run / f"{name}.log"
        record = {"name": name, "expected_exit": expected, "log": log.name}
        report["steps"].append(record)
        save()
        print(f"Running {name}; log: {log}", flush=True)
        started = time.monotonic()
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.run(list(map(str, args)), cwd=cwd, stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=timeout, check=False)
        record.update(exit_code=process.returncode, seconds=round(time.monotonic()-started, 2),
                      passed=process.returncode == expected)
        save()
        if process.returncode != expected:
            raise RuntimeError(f"{name}: expected exit {expected}, got {process.returncode}; see {log.name}")
        return log

    try:
        save()
        print(f"macOS test evidence: {run}", flush=True)
        environment = run / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / "bin" / "python"
        cli = environment / "bin" / "pandas-processor"
        step("install", [python, "-m", "pip", "install", ".[test]"], cwd=root, timeout=1200)
        step("versions", [python, "-m", "pip", "freeze"], cwd=run)
        step("help", [cli, "--help"], cwd=run)
        doctor_log = step("doctor", [cli, "doctor"], cwd=run)
        report["doctor"] = json.loads(doctor_log.read_text(encoding="utf-8"))
        if report["doctor"].get("status") != "success":
            raise RuntimeError("doctor did not report success")

        junit = run / "pytest.xml"
        step("pytest", [python, "-m", "pytest", "-q", "--junitxml", junit], cwd=root)
        suites = ET.parse(junit).getroot()
        report["pytest"] = {key: sum(int(suite.get(key, "0")) for suite in suites.iter("testsuite"))
                            for key in ("tests", "failures", "errors", "skipped")}
        if not report["pytest"]["tests"] or report["pytest"]["failures"] or report["pytest"]["errors"]:
            raise RuntimeError("pytest results are empty or contain failures")

        fixture = root / "tests" / "fixtures"
        source = fixture / "sales.csv"
        schema = root / "specs" / "schema.example.json"
        contract = fixture / "result.json"
        for suffix in ("csv", "xlsx"):
            output = run / f"cleaned.{suffix}"
            step(f"clean-{suffix}", [cli, "clean", source, "--schema", schema,
                                     "--contract", contract, "--output", output], cwd=run)
            sheet = ["--sheet", "Cleaned"] if suffix == "xlsx" else []
            after_sheet = ["--after-sheet", "Cleaned"] if suffix == "xlsx" else []
            step(f"validate-{suffix}", [cli, "validate-result", output, "--contract", contract, *sheet], cwd=run)
            step(f"totals-{suffix}", [cli, "totals", source, output, "--columns", "amount", *after_sheet], cwd=run)
        step("exceptions", [cli, "exceptions", fixture / "invalid.csv", "--schema", schema,
                            "--output", run / "exceptions.xlsx"], cwd=run, expected=2)
        report["status"] = "passed"
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError, ET.ParseError) as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
        print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
