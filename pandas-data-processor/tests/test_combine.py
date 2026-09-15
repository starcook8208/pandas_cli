"""Concat compatibility and guarded join behavior."""
from pathlib import Path

import pandas as pd
import pytest

from errors import SkillError
from operations import combine, discover, safe_merge
from table_io import read_table, write_tables


def test_combine_csv_and_xlsx_preserves_sources(tmp_path, fixtures, schema):
    csv_path = tmp_path / "first.csv"
    csv_path.write_bytes((fixtures / "sales.csv").read_bytes())
    xlsx = tmp_path / "second.xlsx"
    second = read_table(csv_path)
    second["employee_id"] = ["001236", "001237"]
    write_tables({"Sales": second}, xlsx)
    result = combine(discover([str(tmp_path)]), schema=schema)
    assert len(result) == 4
    assert set(result.source_file) == {str(csv_path.resolve()), str(xlsx.resolve())}
    assert result.source_row.tolist() == [2, 3, 2, 3]
    assert result.employee_id.tolist() == ["001234", "001235", "001236", "001237"]


def test_unique_key_overlap_across_inputs(tmp_path, fixtures, schema):
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    first.write_bytes((fixtures / "sales.csv").read_bytes())
    second.write_bytes(first.read_bytes())
    with pytest.raises(SkillError) as caught:
        combine([first, second], schema=schema)
    assert caught.value.code == "DUPLICATE_KEY"


def test_glob_and_multiple_sheets(tmp_path):
    path = tmp_path / "sheets.xlsx"
    write_tables({"A": pd.DataFrame({"id": ["01"]}), "B": pd.DataFrame({"id": ["02"]})}, path)
    result = combine(discover([str(tmp_path / "*.xlsx")]), all_sheets=True)
    assert result.source_sheet.tolist() == ["A", "B"]


def test_schema_mismatch_stops_export(tmp_path, cli):
    left, right = tmp_path / "a.csv", tmp_path / "b.csv"
    left.write_text("id,amount\n001,1\n", encoding="utf-8")
    right.write_text("id,total\n002,2\n", encoding="utf-8")
    output = tmp_path / "out.xlsx"
    result = cli("combine_files", left, right, "--output", output, expected=2)
    assert result["error"]["code"] == "SCHEMA_MISMATCH"
    assert not output.exists()


def test_discovery_cannot_include_output(tmp_path):
    path = tmp_path / "out.csv"
    path.write_text("id\n001\n", encoding="utf-8")
    with pytest.raises(SkillError, match="Output is among"):
        discover([str(tmp_path)], path)


def test_merge_cardinality_and_lineage():
    left = pd.DataFrame({"id": ["a", "b"], "amount": [1, 2]})
    right = pd.DataFrame({"id": ["a", "c"], "name": ["A", "C"]})
    merged, audit = safe_merge(left, right, on=["id"], cardinality="many_to_one", expected_rows=2)
    assert audit["unmatched_left_keys"] == 1
    assert audit["unmatched_right_keys"] == 1
    assert "source_file_left" in merged and "source_file_right" in merged


@pytest.mark.parametrize("cardinality,expected", [("many_to_one", 2), ("many_to_many", 2)])
def test_merge_unexpected_multiplication(cardinality, expected):
    left = pd.DataFrame({"id": ["a", "a"]})
    right = pd.DataFrame({"id": ["a", "a"]})
    with pytest.raises(SkillError) as caught:
        safe_merge(left, right, on=["id"], cardinality=cardinality, expected_rows=expected)
    assert caught.value.code == "MERGE_CARDINALITY_ERROR"


def test_merge_null_keys_stop():
    frame = pd.DataFrame({"id": [None]})
    with pytest.raises(SkillError, match="Null merge keys"):
        safe_merge(frame, frame, on=["id"], cardinality="one_to_one", expected_rows=1)
