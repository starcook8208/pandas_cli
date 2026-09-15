"""Shared structured errors and strict JSON serialization for pandas_processor."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class SkillError(Exception):
    """An actionable, machine-readable processing failure."""

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.details = details

    def payload(self) -> dict[str, Any]:
        return {"status": "error", "error": {
            "code": self.code, "file": None, "sheet": None, "column": None,
            "message": str(self), **self.details,
        }}


def json_value(value: Any) -> Any:
    """Convert pandas scalars without emitting nonstandard NaN JSON."""
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        return json_value(value.item())
    return str(value)


def dumps(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=True, allow_nan=False)


def read_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise SkillError("FILE_NOT_FOUND", "JSON file not found.", file=str(path))
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        raise SkillError("SCHEMA_MISMATCH", f"Invalid UTF-8 JSON: {exc}", file=str(path)) from exc
    if not isinstance(obj, dict):
        raise SkillError("SCHEMA_MISMATCH", "JSON root must be an object.", file=str(path))
    return obj
