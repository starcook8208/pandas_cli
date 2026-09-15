"""Schema normalization, row exceptions, result contracts, and exact totals."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
from typing import Any
import re

import pandas as pd

from .errors import SkillError, json_value
from .table_io import PROVENANCE, add_provenance

EXCEPTION_COLUMNS = ["source", "row", "field", "original_value", "error_code", "reason",
                     "source_file", "source_sheet", "source_row"]
TYPES = {"string", "number", "integer", "datetime", "boolean"}


def column_rules(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Check the schema itself before using it as a data contract."""
    allowed = {"required_columns", "optional_columns", "unique_key", "allow_extra_columns"}
    if set(schema) - allowed or not isinstance(schema.get("required_columns"), dict):
        raise SkillError("SCHEMA_MISMATCH", "Schema needs required_columns; unknown schema keys are prohibited.")
    if not isinstance(schema.get("optional_columns", {}), dict):
        raise SkillError("SCHEMA_MISMATCH", "optional_columns must be an object.")
    if set(schema["required_columns"]) & set(schema.get("optional_columns", {})):
        raise SkillError("SCHEMA_MISMATCH", "Required and optional columns overlap.")
    rules = {}
    for name, rule in {**schema["required_columns"], **schema.get("optional_columns", {})}.items():
        rule = {"dtype": rule} if isinstance(rule, str) else rule
        if not isinstance(rule, dict) or rule.get("dtype") not in TYPES:
            raise SkillError("SCHEMA_MISMATCH", "Unknown or missing dtype.", column=name)
        if set(rule) - {"dtype", "nullable", "min", "max", "enum", "pattern", "format"}:
            raise SkillError("SCHEMA_MISMATCH", "Unknown column rule.", column=name)
        if not isinstance(rule.get("nullable", True), bool):
            raise SkillError("SCHEMA_MISMATCH", "nullable must be boolean.", column=name)
        if "enum" in rule and not isinstance(rule["enum"], list):
            raise SkillError("SCHEMA_MISMATCH", "enum must be an array.", column=name)
        if "pattern" in rule:
            try:
                re.compile(rule["pattern"])
            except (re.error, TypeError) as exc:
                raise SkillError("SCHEMA_MISMATCH", "Invalid pattern.", column=name) from exc
        if "format" in rule and (rule["dtype"] != "datetime" or not isinstance(rule["format"], str)):
            raise SkillError("SCHEMA_MISMATCH", "format requires datetime dtype and a string.", column=name)
        for bound in ("min", "max"):
            if bound in rule and (rule["dtype"] not in {"number", "integer"} or
                                  isinstance(rule[bound], bool) or not isinstance(rule[bound], (int, float))):
                raise SkillError("SCHEMA_MISMATCH", "min/max require numeric bounds and dtype.", column=name)
        if "min" in rule and "max" in rule and rule["min"] > rule["max"]:
            raise SkillError("SCHEMA_MISMATCH", "min exceeds max.", column=name)
        rules[name] = rule
    keys = schema.get("unique_key", [])
    if not isinstance(keys, list) or any(not isinstance(k, str) or k not in rules for k in keys):
        raise SkillError("SCHEMA_MISMATCH", "unique_key must name declared columns.")
    if not isinstance(schema.get("allow_extra_columns", True), bool):
        raise SkillError("SCHEMA_MISMATCH", "allow_extra_columns must be boolean.")
    return rules


def validate_frame(frame: pd.DataFrame, schema: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return typed valid rows and every field issue, preserving raw values and lineage."""
    rules = column_rules(schema)
    missing = set(schema["required_columns"]) - set(frame.columns)
    if missing:
        raise SkillError("SCHEMA_MISMATCH", "Required columns are missing.", columns=sorted(missing))
    extra = set(frame.columns) - set(rules) - set(PROVENANCE)
    if extra and not schema.get("allow_extra_columns", True):
        raise SkillError("SCHEMA_MISMATCH", "Unexpected columns.", columns=sorted(extra))
    raw = add_provenance(frame).reset_index(drop=True)
    normalized = raw.copy()
    failures: list[dict[str, Any]] = []
    invalid = pd.Series(False, index=raw.index)

    def record(mask: pd.Series, field: str, code: str, reason: str) -> None:
        nonlocal invalid
        mask = mask.fillna(False)
        invalid |= mask
        for index in raw.index[mask]:
            item = raw.loc[index]
            failures.append({"source": item["source_file"], "row": item["source_row"],
                             "field": field, "original_value": json_value(item[field]),
                             "error_code": code, "reason": reason,
                             **{key: item[key] for key in PROVENANCE}})

    for name, rule in rules.items():
        if name not in raw:
            continue
        values = raw[name]
        dtype = rule["dtype"]
        if dtype in {"number", "integer"}:
            converted = pd.to_numeric(values, errors="coerce")
            bad = values.notna() & (converted.isna() | converted.isin([float("inf"), -float("inf")]))
            if dtype == "integer":
                bad |= converted.notna() & (converted % 1 != 0)
            # Reject silent precision loss, e.g. long decimal strings or oversized integers.
            for index in values.index[values.notna() & ~bad]:
                try:
                    if Decimal(str(values.at[index])) != Decimal(str(converted.at[index])):
                        bad.at[index] = True
                except InvalidOperation:
                    bad.at[index] = True
            record(bad, name, "NUMERIC_PARSE_ERROR", f"Expected finite {dtype}.")
            normalized[name] = converted.mask(bad)
        elif dtype == "datetime":
            converted = pd.to_datetime(values, errors="coerce", format=rule.get("format", "ISO8601"), utc=True)
            record(values.notna() & converted.isna(), name, "DATE_PARSE_ERROR", "Invalid date for declared format.")
            # Normalize to UTC without timezone so validated results can be written to XLSX.
            normalized[name] = converted.dt.tz_localize(None)
        elif dtype == "boolean":
            converted = values.astype("string").str.lower().map({"true": True, "false": False}).astype("boolean")
            record(values.notna() & converted.isna(), name, "DTYPE_ERROR", "Expected true or false.")
            normalized[name] = converted
        else:
            normalized[name] = values.astype("string")
        if not rule.get("nullable", True):
            record(values.isna(), name, "SCHEMA_MISMATCH", "Null is prohibited.")
        if "enum" in rule:
            record(values.notna() & ~normalized[name].isin(rule["enum"]), name, "SCHEMA_MISMATCH", "Value outside enum.")
        if "pattern" in rule:
            record(values.notna() & ~values.astype("string").str.fullmatch(rule["pattern"], na=False),
                   name, "SCHEMA_MISMATCH", "Value does not match pattern.")
        for bound, compare in (("min", "lt"), ("max", "gt")):
            if bound in rule:
                record(getattr(normalized[name], compare)(rule[bound]), name, "SCHEMA_MISMATCH", f"Violates {bound}.")
    keys = schema.get("unique_key", [])
    if keys:
        if not set(keys).issubset(raw.columns):
            raise SkillError("SCHEMA_MISMATCH", "A unique key column is absent.")
        duplicate = normalized.duplicated(keys, keep=False)
        for name in keys:
            record(raw[name].isna(), name, "DUPLICATE_KEY", "Unique keys cannot be null.")
        record(duplicate, keys[0], "DUPLICATE_KEY", "Duplicate composite key; all members retained as exceptions.")
    return normalized.loc[~invalid].copy(), pd.DataFrame(failures, columns=EXCEPTION_COLUMNS)


def total(frame: pd.DataFrame, column: str) -> Decimal:
    """Use Decimal on original lexical values; null/nonfinite totals are a hard failure."""
    if column not in frame:
        raise SkillError("SCHEMA_MISMATCH", "Total column missing.", column=column)
    if frame[column].isna().any():
        raise SkillError("TOTAL_MISMATCH", "Cannot certify a total containing missing values.", column=column)
    numbers = []
    for value in frame[column]:
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise SkillError("NUMERIC_PARSE_ERROR", "Total contains nonnumeric data.", column=column) from exc
        if not number.is_finite():
            raise SkillError("NUMERIC_PARSE_ERROR", "Total contains nonfinite data.", column=column)
        numbers.append(number)
    if not numbers:
        return Decimal(0)
    # Decimal's default precision (28) is insufficient for arbitrary source totals.
    highest = max(number.adjusted() for number in numbers)
    lowest = min(number.as_tuple().exponent for number in numbers)
    with localcontext() as context:
        context.prec = max(28, highest - lowest + len(str(len(numbers))) + 3)
        return sum(numbers, Decimal(0))


def compare_frames(before: pd.DataFrame, after: pd.DataFrame, columns: list[str],
                   atol: str = "0", rtol: str = "0") -> dict[str, Any]:
    absolute, relative = Decimal(atol), Decimal(rtol)
    if not absolute.is_finite() or not relative.is_finite() or absolute < 0 or relative < 0:
        raise SkillError("INVALID_ARGUMENT", "Tolerances must be finite and nonnegative.")
    results = {}
    for column in columns:
        left, right = total(before, column), total(after, column)
        results[column] = {"before_total": str(left), "after_total": str(right),
                           "difference": str(right-left),
                           "pass": abs(left-right) <= absolute + relative * abs(left)}
    if not all(item["pass"] for item in results.values()):
        raise SkillError("TOTAL_MISMATCH", "Totals differ beyond tolerance.", totals=results)
    return results


def validate_result_frame(frame: pd.DataFrame, contract: dict[str, Any],
                          exception_count: int = 0) -> dict[str, Any]:
    allowed = {"row_count", "required_columns", "duplicate_count", "duplicate_keys", "null_counts",
               "unique_ids", "totals", "exception_count"}
    if not contract or set(contract) - allowed:
        raise SkillError("SCHEMA_MISMATCH", "Result contract is empty or has unknown checks.")
    for key in ("row_count", "duplicate_count", "exception_count"):
        if key in contract and (type(contract[key]) is not int or contract[key] < 0):
            raise SkillError("SCHEMA_MISMATCH", f"{key} must be a nonnegative integer.")
    for key in ("required_columns", "duplicate_keys"):
        if key in contract and (not isinstance(contract[key], list) or
                                any(not isinstance(v, str) for v in contract[key])):
            raise SkillError("SCHEMA_MISMATCH", f"{key} must be an array of column names.")
    for key in ("null_counts", "unique_ids", "totals"):
        if key in contract and not isinstance(contract[key], dict):
            raise SkillError("SCHEMA_MISMATCH", f"{key} must be an object.")
    if any(type(value) is not int or value < 0 for value in contract.get("null_counts", {}).values()):
        raise SkillError("SCHEMA_MISMATCH", "null_counts must contain nonnegative integers.")
    if any(not isinstance(value, list) for value in contract.get("unique_ids", {}).values()):
        raise SkillError("SCHEMA_MISMATCH", "unique_ids must contain arrays of IDs.")
    for rule in contract.get("totals", {}).values():
        if isinstance(rule, dict) and ("value" not in rule or set(rule) - {"value", "atol", "rtol"}):
            raise SkillError("SCHEMA_MISMATCH", "A total rule requires value and supports only atol/rtol.")
    checks: dict[str, Any] = {}

    def check(name: str, actual: Any, expected: Any, code: str) -> None:
        checks[name] = {"actual": actual, "expected": expected, "pass": actual == expected}
        if actual != expected:
            raise SkillError(code, f"Result check failed: {name}.", checks=checks)

    if "row_count" in contract:
        check("row_count", len(frame), contract["row_count"], "ROW_COUNT_MISMATCH")
    required = contract.get("required_columns", [])
    if not set(required).issubset(frame.columns):
        raise SkillError("SCHEMA_MISMATCH", "Result lacks required columns.")
    if "required_columns" in contract:
        checks["required_columns"] = {"pass": True}
    data_cols = [c for c in frame.columns if c not in PROVENANCE]
    if "duplicate_count" in contract:
        keys = contract.get("duplicate_keys", data_cols)
        if not keys or not set(keys).issubset(frame.columns):
            raise SkillError("SCHEMA_MISMATCH", "Invalid duplicate_keys.")
        check("duplicate_count", int(frame.duplicated(keys, keep=False).sum()), contract["duplicate_count"], "DUPLICATE_KEY")
    for column, expected in contract.get("null_counts", {}).items():
        if column not in frame:
            raise SkillError("SCHEMA_MISMATCH", "Null-check column missing.", column=column)
        check(f"null_counts.{column}", int(frame[column].isna().sum()), expected, "VALIDATION_FAILED")
    for column, expected in contract.get("unique_ids", {}).items():
        if column not in frame or frame[column].isna().any() or frame[column].duplicated().any():
            raise SkillError("DUPLICATE_KEY", "IDs must be present, unique, and nonnull.", column=column)
        check(f"unique_ids.{column}", sorted(frame[column].astype(str).tolist()), sorted(map(str, expected)), "VALIDATION_FAILED")
    for column, rule in contract.get("totals", {}).items():
        rule = rule if isinstance(rule, dict) else {"value": rule}
        expected = pd.DataFrame({column: [str(rule["value"])]})
        checks[f"totals.{column}"] = compare_frames(expected, frame, [column], str(rule.get("atol", 0)), str(rule.get("rtol", 0)))[column]
    if "exception_count" in contract:
        check("exception_count", exception_count, contract["exception_count"], "VALIDATION_FAILED")
    if not checks:
        raise SkillError("SCHEMA_MISMATCH", "Result contract contains no executable checks.")
    return checks
