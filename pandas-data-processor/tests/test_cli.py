"""Installed CLI, workspace launcher, and legacy scripts share the same contracts."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import ROOT
from pandas_processor.entry import SUBCOMMANDS

CONSOLE = Path(sys.executable).parent / ("pandas-processor.exe" if os.name == "nt" else "pandas-processor")


def invoke(args, *, cwd, expected=0):
    """Run a real process without relying on virtualenv activation or PYTHONPATH."""
    environment = {key: value for key, value in os.environ.items() if key not in {"VIRTUAL_ENV", "PYTHONPATH"}}
    result = subprocess.run(list(map(str, args)), cwd=cwd, env=environment,
                            capture_output=True, text=True, encoding="utf-8", timeout=45)
    assert result.returncode == expected, (result.stdout, result.stderr)
    assert not result.stderr, result.stderr
    return result.stdout


def test_installed_entry_and_module_outside_checkout(tmp_path):
    assert CONSOLE.is_file(), "Install the package before running CLI integration tests."
    installed = invoke([CONSOLE, "--version"], cwd=tmp_path)
    module = invoke([sys.executable, "-I", "-m", "pandas_processor", "--version"], cwd=tmp_path)
    assert installed == module
    assert "0.1.0" in installed


@pytest.mark.parametrize("command", [*SUBCOMMANDS, "export", "doctor"])
def test_subcommand_help(command, tmp_path):
    output = invoke([CONSOLE, command, "--help"], cwd=tmp_path)
    assert "usage:" in output


def test_root_help_does_not_import_data_engine(tmp_path):
    code = "from pandas_processor.entry import main; import sys; main([]); assert 'pandas' not in sys.modules"
    result = invoke([sys.executable, "-I", "-c", code], cwd=tmp_path)
    assert "Commands:" in result


@pytest.mark.parametrize("args", [["unknown"], ["--version", "extra"], ["doctor", "extra"], ["inspect"]])
def test_structured_usage_errors(args, tmp_path):
    result = json.loads(invoke([CONSOLE, *args], cwd=tmp_path, expected=2))
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_ARGUMENT"


def test_doctor_identifies_actual_interpreter(tmp_path):
    result = json.loads(invoke([CONSOLE, "doctor"], cwd=tmp_path))
    assert Path(result["python"]).resolve() == Path(sys.executable).resolve()
    assert all(item["status"] == "ok" for item in result["dependencies"].values())


def test_cli_csv_xlsx_workflow(fixtures, tmp_path):
    source = tmp_path / "來源 data & values.csv"
    source.write_bytes((fixtures / "sales.csv").read_bytes())
    original = source.read_bytes()
    schema = ROOT / "specs" / "schema.example.json"
    contract = fixtures / "result.json"

    def run(*args, expected=0):
        return json.loads(invoke([CONSOLE, *args], cwd=tmp_path, expected=expected))

    assert run("inspect", source, "--sample", "1")["sample"][0]["employee_id"] == "001234"
    assert run("profile", source, "--sample", "0")["duplicate_count"] == 0
    assert run("validate", source, "--schema", schema)["valid_rows"] == 2
    workbook = tmp_path / "combined.xlsx"
    assert run("combine", source, "--schema", schema, "--output", workbook)["files"] == 1
    assert run("workbook", workbook)["sheets"][0]["rows"] == 2
    report = tmp_path / "report.xlsx"
    assert run("clean", source, "--schema", schema, "--contract", contract, "--output", report,
               "--group-by", "department", "--sum-columns", "amount")["validation_status"] == "passed"
    run("validate-result", report, "--sheet", "Cleaned", "--contract", contract,
        "--exceptions-file", report, "--exceptions-sheet", "Exceptions")
    assert run("totals", source, report, "--after-sheet", "Summary", "--columns", "amount")["totals"]["amount"]["pass"]
    csv = tmp_path / "cleaned.csv"
    run("export", source, "--schema", schema, "--contract", contract, "--output", csv)
    run("totals", source, csv, "--columns", "amount")
    assert source.read_bytes() == original


def test_cli_failures_keep_diagnostics_but_block_report(fixtures, tmp_path):
    schema = ROOT / "specs" / "schema.example.json"
    for command, flags, code in [
        ("duplicates", ["--keys", "employee_id"], "DUPLICATE_KEY"),
        ("exceptions", ["--schema", schema], "VALIDATION_FAILED"),
    ]:
        output = tmp_path / f"{command}.xlsx"
        result = json.loads(invoke([CONSOLE, command, fixtures / "invalid.csv", *flags, "--output", output],
                                   cwd=tmp_path, expected=2))
        assert result["error"]["code"] == code
        assert output.exists()
    report = tmp_path / "must-not-exist.xlsx"
    result = json.loads(invoke([CONSOLE, "clean", fixtures / "invalid.csv", "--schema", schema,
                               "--contract", fixtures / "result.json", "--output", report], cwd=tmp_path, expected=2))
    assert result["error"]["code"] == "VALIDATION_FAILED"
    assert not report.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows workspace launcher")
def test_windows_launcher_no_activation_and_relative_paths(fixtures, tmp_path):
    filename = "測試 data & values.csv"
    (tmp_path / filename).write_bytes((fixtures / "sales.csv").read_bytes())
    prefix = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", ROOT / "pandas-processor.cmd"]
    result = json.loads(invoke([*prefix, "inspect", filename], cwd=tmp_path))
    assert result["rows"] == 2
    assert Path(result["file"]) == (tmp_path / filename).resolve()
    failure = json.loads(invoke([*prefix, "validate", filename], cwd=tmp_path, expected=2))
    assert failure["error"]["code"] == "INVALID_ARGUMENT"
