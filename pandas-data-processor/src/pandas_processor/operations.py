"""Bounded metadata, schema-compatible concat, and guarded joins."""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import pandas as pd

from .errors import SkillError
from .table_io import FORMATS, PROVENANCE, add_provenance, iter_tables, read_table, workbook_sheets
from .validation import validate_frame


def inspect(path: str | Path, *, sample: int = 3, **kwargs: Any) -> dict[str, Any]:
    """Compute exact row/null counts using CSV chunks, and bounded sample inference."""
    if not 0 <= sample <= 20:
        raise SkillError("INVALID_ARGUMENT", "sample must be between 0 and 20.")
    rows = 0
    nulls: dict[str, int] = {}
    samples: list[pd.DataFrame] = []
    sampled = 0
    headers: list[str] = []
    dtypes: dict[str, str] = {}
    for frame in iter_tables(path, **kwargs):
        rows += len(frame)
        headers = list(frame.columns)
        dtypes = {str(c): str(t) for c, t in frame.dtypes.items()}
        for name, count in frame.isna().sum().items():
            nulls[name] = nulls.get(name, 0) + int(count)
        part = frame.head(max(0, sample-sampled))
        samples.append(part)
        sampled += len(part)
    preview = pd.concat(samples, ignore_index=True) if samples else pd.DataFrame()
    return {"file": str(Path(path).resolve()), "size_bytes": Path(path).stat().st_size,
            "rows": rows, "columns": len(headers), "headers": headers, "storage_dtypes": dtypes,
            "inferred_dtypes": {c: pd.api.types.infer_dtype(preview[c].dropna()) for c in preview},
            "dtype_scope": "sample; raw values are loaded as strings", "null_counts": nulls,
            "duplicate_count": None, "duplicate_scope": "not computed; use find_duplicates.py for exact counts",
            "sample": preview.to_dict(orient="records"), "sample_rows": len(preview)}


def discover(inputs: list[str], excluded: str | Path | None = None) -> list[Path]:
    paths: set[Path] = set()
    for item in inputs:
        candidate = Path(item)
        if candidate.is_dir():
            found = [p for p in candidate.iterdir() if p.suffix.lower() in FORMATS and not p.name.startswith("~$")]
        elif candidate.is_file():
            found = [candidate]
        else:
            found = [Path(p) for p in glob.glob(item)]
        if not found:
            raise SkillError("FILE_NOT_FOUND", "Input or pattern matched no files.", file=item)
        paths.update(p.resolve() for p in found if p.is_file())
    if excluded is not None and Path(excluded).resolve() in paths:
        raise SkillError("EXPORT_ERROR", "Output is among discovered inputs; use a separate output directory.")
    if not paths:
        raise SkillError("FILE_NOT_FOUND", "No input files.")
    return sorted(paths)


def combine(paths: list[Path], *, all_sheets: bool = False,
            schema: dict[str, Any] | None = None, **kwargs: Any) -> pd.DataFrame:
    frames = []
    expected: set[str] | None = None
    for path in paths:
        sheets = workbook_sheets(path) if all_sheets and path.suffix.lower() == ".xlsx" else [kwargs.get("sheet")]
        for sheet in sheets:
            options = {**kwargs, "sheet": sheet}
            raw = read_table(path, **options)
            columns = set(raw.columns) - set(PROVENANCE)
            if expected is None:
                expected = columns
            elif columns != expected:
                raise SkillError("SCHEMA_MISMATCH", "Column sets differ; concat stopped.", file=str(path), sheet=sheet,
                                 missing=sorted(expected-columns), extra=sorted(columns-expected))
            if schema:
                frame, exceptions = validate_frame(raw, schema)
                if len(exceptions):
                    raise SkillError("VALIDATION_FAILED", "Input has schema violations; run find_exceptions.py.",
                                     file=str(path), sheet=sheet, exception_count=len(exceptions))
            else:
                frame = add_provenance(raw)
            frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    keys = schema.get("unique_key", []) if schema else []
    if keys and result.duplicated(keys, keep=False).any():
        raise SkillError("DUPLICATE_KEY", "Unique keys overlap across input files/sheets; concat not published.",
                         duplicate_count=int(result.duplicated(keys, keep=False).sum()))
    return result


def safe_merge(left: pd.DataFrame, right: pd.DataFrame, *, on: list[str],
               cardinality: str, expected_rows: int, how: str = "left") -> tuple[pd.DataFrame, dict[str, Any]]:
    """Require a row contract even for many-to-many; keep both sides' lineage."""
    if cardinality not in {"one_to_one", "one_to_many", "many_to_one", "many_to_many"}:
        raise SkillError("MERGE_CARDINALITY_ERROR", "Declare a supported cardinality.")
    if how not in {"left", "right", "inner", "outer"} or not on:
        raise SkillError("INVALID_ARGUMENT", "Specify merge keys and left/right/inner/outer join.")
    if not set(on).issubset(left.columns) or not set(on).issubset(right.columns):
        raise SkillError("SCHEMA_MISMATCH", "Merge keys missing.")
    if left[on].isna().any().any() or right[on].isna().any().any():
        raise SkillError("MERGE_CARDINALITY_ERROR", "Null merge keys need an explicit business policy before joining.")
    audit = {"left_rows": len(left), "right_rows": len(right),
             "left_duplicate_key_rows": int(left.duplicated(on, keep=False).sum()),
             "right_duplicate_key_rows": int(right.duplicated(on, keep=False).sum())}
    if not isinstance(expected_rows, int) or isinstance(expected_rows, bool) or expected_rows < 0:
        raise SkillError("INVALID_ARGUMENT", "expected_rows must be a nonnegative integer.")
    if ((cardinality in {"one_to_one", "one_to_many"} and audit["left_duplicate_key_rows"]) or
            (cardinality in {"one_to_one", "many_to_one"} and audit["right_duplicate_key_rows"])):
        raise SkillError("MERGE_CARDINALITY_ERROR", "Duplicate keys violate declared cardinality.", audit=audit)
    # Predict the join size using per-key counts before allocating a potentially huge result.
    left_counts = left.groupby(on, dropna=False, observed=True).size().rename("_left_count").reset_index()
    right_counts = right.groupby(on, dropna=False, observed=True).size().rename("_right_count").reset_index()
    counts = left_counts.merge(right_counts, on=on, how="outer", indicator=True, validate="one_to_one")
    predicted = 0
    for _, row in counts.iterrows():
        if row["_merge"] == "both":
            predicted += int(row["_left_count"]) * int(row["_right_count"])
        elif row["_merge"] == "left_only" and how in {"left", "outer"}:
            predicted += int(row["_left_count"])
        elif row["_merge"] == "right_only" and how in {"right", "outer"}:
            predicted += int(row["_right_count"])
    audit["predicted_rows"] = predicted
    if predicted != expected_rows:
        raise SkillError("MERGE_CARDINALITY_ERROR", "Predicted merge size differs from contract; join not allocated.",
                         expected_rows=expected_rows, audit=audit)
    try:
        keys = left[on].drop_duplicates().merge(right[on].drop_duplicates(), on=on, how="outer", indicator=True, validate="one_to_one")
        audit.update(unmatched_left_keys=int((keys["_merge"] == "left_only").sum()),
                     unmatched_right_keys=int((keys["_merge"] == "right_only").sum()))
        result = add_provenance(left).merge(add_provenance(right), on=on, how=how,
                                            validate=cardinality, indicator=True, suffixes=("_left", "_right"))
    except pd.errors.MergeError as exc:
        raise SkillError("MERGE_CARDINALITY_ERROR", str(exc), audit=audit) from exc
    audit["result_rows"] = len(result)
    if len(result) != expected_rows:
        raise SkillError("MERGE_CARDINALITY_ERROR", "Unexpected result row count.", expected_rows=expected_rows, audit=audit)
    return result, audit
