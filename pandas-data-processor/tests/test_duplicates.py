"""Duplicate groups and diagnostic exports are complete and machine-readable."""
from conftest import ROOT
from table_io import read_table
from validation import validate_frame


def test_duplicate_cli_keeps_all_members(cli, fixtures, tmp_path):
    output = tmp_path / "duplicates.csv"
    result = cli("find_duplicates", fixtures / "invalid.csv", "--keys", "employee_id", "--output", output, expected=2)
    assert result["error"]["code"] == "DUPLICATE_KEY"
    duplicate = read_table(output)
    assert len(duplicate) == 2
    assert duplicate.source_row.tolist() == ["2", "3"]
    assert duplicate.amount.tolist() == ["10.25", "oops"]


def test_exceptions_cli_preserves_originals(cli, fixtures, tmp_path):
    output = tmp_path / "exceptions.xlsx"
    result = cli("find_exceptions", fixtures / "invalid.csv", "--schema", ROOT / "specs" / "schema.example.json",
                 "--output", output, expected=2)
    assert result["error"]["exception_count"] >= 4
    frame = read_table(output)
    assert {"oops", "not-a-date"}.issubset(set(frame.original_value.dropna()))
    assert {"source", "row", "field", "original_value", "error_code", "reason"}.issubset(frame.columns)


def test_no_duplicate_and_profile(cli, fixtures):
    assert cli("find_duplicates", fixtures / "sales.csv", "--keys", "employee_id")["duplicate_count"] == 0
    profile = cli("profile_data", fixtures / "sales.csv", "--sample", "0")
    assert profile["rows"] == 2 and profile["sample"] == []
    assert profile["distinct_counts"]["employee_id"] == 2


def test_normalized_duplicate_keys():
    import pandas as pd
    valid, errors = validate_frame(pd.DataFrame({"id": ["1", "01"]}),
                                  {"required_columns": {"id": "integer"}, "unique_key": ["id"]})
    assert valid.empty
    assert errors.error_code.tolist() == ["DUPLICATE_KEY", "DUPLICATE_KEY"]
