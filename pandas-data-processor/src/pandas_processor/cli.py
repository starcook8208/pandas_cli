"""Shared argument definitions and dispatch for the ten focused commands."""
from __future__ import annotations

import argparse
from decimal import InvalidOperation
from pathlib import Path
from typing import Any
from zipfile import BadZipFile

import pandas as pd

from .errors import SkillError, dumps, read_json
from .operations import combine, discover, inspect
from .table_io import PROVENANCE, add_provenance, read_table, workbook_sheets, write_tables
from .validation import compare_frames, validate_frame, validate_result_frame

COMMANDS = {
    "inspect_table": "Return exact row/null counts and a bounded sample.",
    "inspect_workbook": "Inspect every XLSX sheet without dumping whole tables.",
    "profile_data": "Profile a table with exact duplicates and per-column counts (in memory).",
    "combine_files": "Concatenate matching CSV/XLSX schemas and retain source lineage.",
    "validate_schema": "Validate and safely normalize a table against a JSON schema.",
    "validate_result": "Enforce row, null, ID, total, duplicate, and exception contracts.",
    "compare_totals": "Compare exact decimal totals; mismatch is a hard failure.",
    "find_duplicates": "Identify every member of duplicate-key groups, without deleting rows.",
    "find_exceptions": "Export schema violations with original values and source locations.",
    "export_report": "Validate and export Raw/Cleaned/Summary/Exceptions sheets.",
}


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SkillError("INVALID_ARGUMENT", message)


def parser_for(command: str, *, prog: str | None = None) -> Parser:
    parser = Parser(description=COMMANDS[command], prog=prog, allow_abbrev=False)
    if command == "combine_files":
        parser.add_argument("inputs", nargs="+", help="Paths, nonrecursive directories, or quoted glob patterns")
    elif command == "compare_totals":
        parser.add_argument("before")
        parser.add_argument("after")
        parser.add_argument("--after-sheet")
    else:
        parser.add_argument("input")
    parser.add_argument("--sheet", help="Exact XLSX sheet name; defaults to first sheet")
    parser.add_argument("--header", type=int, default=0, help="Zero-based header row/CSV record")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--usecols", nargs="+", help="Read only these columns")
    parser.add_argument("--chunksize", type=int, default=100_000, help="CSV read chunk size; only inspect stays bounded")
    if command in {"inspect_table", "inspect_workbook", "profile_data"}:
        parser.add_argument("--sample", type=int, default=3, help="0..20 sample records")
    if command in {"combine_files", "validate_schema", "find_exceptions", "export_report"}:
        parser.add_argument("--schema", required=command in {"validate_schema", "find_exceptions", "export_report"})
    if command in {"combine_files", "find_duplicates", "find_exceptions", "export_report"}:
        parser.add_argument("--output", required=command in {"combine_files", "find_exceptions", "export_report"})
        parser.add_argument("--overwrite", action="store_true", help="Replace an existing output, never a source")
        parser.add_argument("--spreadsheet-safe-csv", action="store_true", help="Prefix formula-like CSV strings with apostrophes")
    if command == "combine_files":
        parser.add_argument("--all-sheets", action="store_true")
    if command == "find_duplicates":
        parser.add_argument("--keys", nargs="+", required=True)
    if command == "compare_totals":
        parser.add_argument("--columns", nargs="+", required=True)
        parser.add_argument("--atol", default="0")
        parser.add_argument("--rtol", default="0")
    if command in {"validate_result", "export_report"}:
        parser.add_argument("--contract", required=True, help="Result expectations JSON")
    if command == "validate_result":
        parser.add_argument("--exceptions-file", help="Exception dataset for actual issue count")
        parser.add_argument("--exceptions-sheet", help="Exact sheet name in exceptions XLSX")
    if command == "export_report":
        parser.add_argument("--allow-exceptions", action="store_true", help="Explicitly export valid subset plus Exceptions")
        parser.add_argument("--group-by", nargs="+")
        parser.add_argument("--sum-columns", nargs="+")
    return parser


def options(args: argparse.Namespace) -> dict[str, Any]:
    return dict(sheet=args.sheet, header=args.header, encoding=args.encoding,
                sep=args.delimiter, usecols=args.usecols, chunksize=args.chunksize)


def publish(tables: dict[str, pd.DataFrame], args: argparse.Namespace, sources: list[str | Path]) -> dict[str, Any]:
    # JSON controls are inputs too and must never be overwritten by an export.
    protected = sources + [getattr(args, key) for key in ("schema", "contract") if getattr(args, key, None)]
    return write_tables(tables, args.output, sources=protected, overwrite=args.overwrite,
                        spreadsheet_safe_csv=args.spreadsheet_safe_csv)


def execute(command: str, args: argparse.Namespace) -> dict[str, Any]:
    opts = options(args)
    if command == "inspect_table":
        return inspect(args.input, sample=args.sample, **opts)
    if command == "inspect_workbook":
        return {"file": str(Path(args.input).resolve()), "sheets": [
            {"name": sheet, **inspect(args.input, sample=args.sample, **{**opts, "sheet": sheet})}
            for sheet in workbook_sheets(args.input)]}
    if command == "combine_files":
        if args.all_sheets and args.sheet:
            raise SkillError("INVALID_ARGUMENT", "Use --all-sheets or --sheet, not both.")
        paths = discover(args.inputs, args.output)
        frame = combine(paths, all_sheets=args.all_sheets,
                        schema=read_json(args.schema) if args.schema else None, **opts)
        return {**publish({"Combined": frame}, args, paths), "files": len(paths),
                "compatibility": "schema validated" if args.schema else "column sets only; raw string dtypes"}
    if command == "compare_totals":
        return {"totals": compare_frames(read_table(args.before, **opts),
                                          read_table(args.after, **{**opts, "sheet": args.after_sheet}),
                                          args.columns, args.atol, args.rtol)}
    frame = read_table(args.input, **opts)
    if command == "profile_data":
        business = [c for c in frame if c not in PROVENANCE]
        return {**inspect(args.input, sample=args.sample, **opts),
                "duplicate_count": int(frame.duplicated(business, keep=False).sum()),
                "duplicate_scope": "all members of exact duplicate business rows; full dataset",
                "memory_bytes": int(frame.memory_usage(deep=True).sum()),
                "distinct_counts": {c: int(frame[c].nunique(dropna=True)) for c in frame}}
    if command == "find_duplicates":
        if not set(args.keys).issubset(frame.columns):
            raise SkillError("SCHEMA_MISMATCH", "Duplicate key column missing.")
        mask = frame.duplicated(args.keys, keep=False)
        duplicates = add_provenance(frame).loc[mask]
        output = publish({"Duplicates": duplicates}, args, [args.input]) if args.output else {}
        if len(duplicates):
            raise SkillError("DUPLICATE_KEY", "Duplicate groups found.", duplicate_count=len(duplicates), **output)
        return {"duplicate_count": 0, **output}
    if command == "validate_result":
        count = len(read_table(args.exceptions_file, sheet=args.exceptions_sheet)) if args.exceptions_file else 0
        return {"checks": validate_result_frame(frame, read_json(args.contract), count)}
    cleaned, exceptions = validate_frame(frame, read_json(args.schema))
    counts = {"raw_rows": len(frame), "valid_rows": len(cleaned),
              "invalid_rows": len(frame)-len(cleaned), "exception_count": len(exceptions)}
    if command == "validate_schema":
        if len(exceptions):
            raise SkillError("VALIDATION_FAILED", "Schema violations found; export full issues with find_exceptions.py.",
                             **counts, sample=exceptions.head(10).to_dict("records"))
        return counts
    if command == "find_exceptions":
        output = publish({"Exceptions": exceptions}, args, [args.input])
        if len(exceptions):
            raise SkillError("VALIDATION_FAILED", "Exceptions exported for review.", **counts, **output)
        return {**counts, **output}
    if len(exceptions) and not args.allow_exceptions:
        raise SkillError("VALIDATION_FAILED", "No report written; inspect exceptions or explicitly allow a valid subset.", **counts)
    checks = validate_result_frame(cleaned, read_json(args.contract), len(exceptions))
    tables = {"Raw": add_provenance(frame), "Cleaned": cleaned}
    if bool(args.group_by) != bool(args.sum_columns):
        raise SkillError("INVALID_ARGUMENT", "--group-by and --sum-columns must be used together.")
    if args.group_by:
        if not set(args.group_by + args.sum_columns).issubset(cleaned.columns):
            raise SkillError("SCHEMA_MISMATCH", "Summary columns missing.")
        if any(not pd.api.types.is_numeric_dtype(cleaned[c]) for c in args.sum_columns):
            raise SkillError("DTYPE_ERROR", "Summary amounts must have a numeric schema dtype.")
        summary = cleaned.groupby(args.group_by, dropna=False, observed=True)[args.sum_columns].sum(min_count=1).reset_index()
        # Aggregation promises conservation; exact by default. Missing amounts stop certification.
        compare_frames(cleaned, summary, args.sum_columns)
        tables["Summary"] = summary
    tables["Exceptions"] = exceptions
    if Path(args.output).suffix.lower() == ".csv":
        if len(exceptions) or args.group_by:
            raise SkillError("EXPORT_ERROR", "Use XLSX to retain Summary/Exceptions; CSV supports Cleaned only.")
        tables = {"Cleaned": cleaned}
    return {**publish(tables, args, [args.input]), **counts, "checks": checks,
            "validation_status": "passed_with_exceptions" if len(exceptions) else "passed",
            "officecli": "optional handoff; presentation not executed"}


def main(command: str, argv: list[str] | None = None, *, prog: str | None = None) -> int:
    """0 = passed, 2 = input/data/validation failure, 3 = runtime or I/O failure."""
    try:
        args = parser_for(command, prog=prog).parse_args(argv)
        result = execute(command, args)
        print(dumps({"status": "success", **result}))
        return 0
    except SkillError as exc:
        print(dumps(exc.payload()))
        return 3 if exc.code in {"OUT_OF_MEMORY", "EXPORT_ERROR", "EXCEL_READ_ERROR"} else 2
    except MemoryError:
        print(dumps(SkillError("OUT_OF_MEMORY", "Reduce columns/chunk work or use an out-of-core engine; do not repeat unchanged.").payload()))
        return 3
    except (BadZipFile, OSError) as exc:
        print(dumps(SkillError("EXCEL_READ_ERROR" if isinstance(exc, BadZipFile) else "IO_ERROR", str(exc)).payload()))
        return 3
    except (ValueError, TypeError, KeyError, InvalidOperation, LookupError) as exc:
        print(dumps(SkillError("INVALID_ARGUMENT", str(exc)).payload()))
        return 2
    except ImportError as exc:
        print(dumps(SkillError("DEPENDENCY_ERROR", str(exc)).payload()))
        return 3
