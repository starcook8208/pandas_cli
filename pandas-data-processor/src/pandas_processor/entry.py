"""Unified CLI; lightweight discovery before importing the data engine."""
from __future__ import annotations

import argparse
from importlib import metadata
import json
import sys

SUBCOMMANDS = {
    "inspect": ("inspect_table", "Inspect a table; return metadata and a bounded sample."),
    "workbook": ("inspect_workbook", "Inspect all sheets of an XLSX workbook."),
    "profile": ("profile_data", "Profile a table, including exact duplicates (in memory)."),
    "combine": ("combine_files", "Combine compatible files and retain source lineage."),
    "validate": ("validate_schema", "Check required columns, types, constraints and keys."),
    "validate-result": ("validate_result", "Check result counts, IDs, totals and exceptions."),
    "totals": ("compare_totals", "Compare before/after totals with declared tolerance."),
    "duplicates": ("find_duplicates", "Find all members of duplicate-key groups."),
    "exceptions": ("find_exceptions", "Export original invalid values and source locations."),
    "clean": ("export_report", "Normalize types, validate, and export cleaned data."),
}
ALIASES = {"export": "clean"}


def version() -> str:
    """Installed version, or an explicit uninstalled-source marker."""
    try:
        return metadata.version("pandas-data-processor")
    except metadata.PackageNotFoundError:
        return "source (not installed)"


def error(code: str, message: str, exit_code: int) -> int:
    print(json.dumps({"status": "error", "error": {
        "code": code, "file": None, "sheet": None, "column": None, "message": message,
    }}, ensure_ascii=True))
    return exit_code


def doctor() -> int:
    """Verify that the interpreter can actually import the declared runtime dependencies."""
    import importlib
    dependencies = {}
    for name in ("pandas", "openpyxl", "xlsxwriter"):
        try:
            module = importlib.import_module(name)
            dependencies[name] = {"status": "ok", "version": module.__version__}
        except (ImportError, OSError) as exc:
            dependencies[name] = {"status": "error", "message": str(exc)}
    healthy = all(item["status"] == "ok" for item in dependencies.values())
    result = {"status": "success" if healthy else "error", "version": version(),
              "python": sys.executable, "python_version": sys.version.split()[0],
              "dependencies": dependencies}
    if not healthy:
        result["error"] = {"code": "DEPENDENCY_ERROR", "file": None, "sheet": None,
                           "column": None, "message": "Runtime dependencies failed to import."}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if healthy else 3


def main(argv: list[str] | None = None) -> int:
    """Dispatch one subcommand without changing the working directory or sys.argv."""
    args = list(sys.argv[1:] if argv is None else argv)
    lines = [f"  {name:17} {description}" for name, (_, description) in SUBCOMMANDS.items()]
    parser = argparse.ArgumentParser(
        prog="pandas-processor", description="Validated CSV/XLSX data cleaning and transformation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Commands:\n" + "\n".join(lines) +
               "\n  doctor            Check interpreter and dependencies.\n"
               "\nUse pandas-processor COMMAND --help for its options.\n"
               "Alias: export = clean. Data commands return JSON; failures exit 2 or 3.",
    )
    parser.add_argument("--version", action="version", version=f"pandas-processor {version()}")
    if not args:
        parser.print_help()
        return 0
    if args[0] in {"-h", "--help", "--version"}:
        if len(args) != 1:
            return error("INVALID_ARGUMENT", "Global help/version must be used alone.", 2)
        parser.parse_args(args)
        return 0
    command = ALIASES.get(args[0], args[0])
    if command == "doctor":
        if args[1:] in (["--help"], ["-h"]):
            print("usage: pandas-processor doctor\nCheck interpreter and runtime dependencies; return JSON.")
            return 0
        if len(args) > 1:
            return error("INVALID_ARGUMENT", "doctor takes no arguments.", 2)
        return doctor()
    if command not in SUBCOMMANDS:
        return error("INVALID_ARGUMENT", f"Unknown command: {args[0]}. Use --help to list commands.", 2)
    try:
        from .cli import main as run_command
    except (ImportError, OSError) as exc:
        return error("DEPENDENCY_ERROR", f"Cannot load data engine: {exc}. Run pandas-processor doctor.", 3)
    return run_command(SUBCOMMANDS[command][0], args[1:], prog=f"pandas-processor {args[0]}")
