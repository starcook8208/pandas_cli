"""Inspection contracts: no full dumps, raw lexical values, proper source offsets."""
import subprocess
import sys

import pandas as pd
import pytest

from conftest import ROOT
from errors import SkillError
from operations import inspect
from table_io import add_provenance, read_table, write_tables
from cli import COMMANDS


def test_csv_metadata_and_leading_zero(fixtures):
    result = inspect(fixtures / "sales.csv", chunksize=1, sample=1)
    assert (result["rows"], result["columns"], result["sample_rows"]) == (2, 4, 1)
    assert result["sample"][0]["employee_id"] == "001234"
    assert result["null_counts"]["amount"] == 0
    assert result["duplicate_count"] is None


def test_xlsx_multiple_sheets_and_identifier(tmp_path, cli):
    path = tmp_path / "book.xlsx"
    write_tables({"Sales": pd.DataFrame({"id": ["001234"], "amount": [10]}),
                  "Other": pd.DataFrame({"id": ["000001"], "amount": [20]})}, path)
    result = cli("inspect_workbook", path)
    assert [s["name"] for s in result["sheets"]] == ["Sales", "Other"]
    frame = add_provenance(read_table(path, sheet="Other"))
    assert frame.loc[0, "id"] == "000001"
    assert frame.loc[0, "source_sheet"] == "Other"
    assert frame.loc[0, "source_row"] == 2


def test_null_tokens_and_custom_header(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("description\nid,note\n001,NA\n002,\n", encoding="utf-8")
    frame = add_provenance(read_table(path, header=1))
    assert frame.loc[0, "note"] == "NA"
    assert pd.isna(frame.loc[1, "note"])
    assert frame["source_row"].tolist() == [3, 4]


@pytest.mark.parametrize("content,code", [
    ("a,a\n1,2\n", "SCHEMA_MISMATCH"),
    ("a,\n1,2\n", "HEADER_NOT_FOUND"),
    ("a,b\n1,2,3\n", "CSV_PARSE_ERROR"),
    ("a,b\n1\n", "CSV_PARSE_ERROR"),
    ("a,b\n\"unclosed,2", "CSV_PARSE_ERROR"),
])
def test_bad_csv(tmp_path, content, code):
    path = tmp_path / "bad.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SkillError) as caught:
        read_table(path)
    assert caught.value.code == code


def test_csv_encoding(tmp_path, cli):
    path = tmp_path / "big5.csv"
    path.write_bytes("姓名,id\n王小明,001\n".encode("cp950"))
    assert cli("inspect_table", path, expected=2)["error"]["code"] == "ENCODING_ERROR"
    assert read_table(path, encoding="cp950").loc[0, "姓名"] == "王小明"


def test_formula_and_missing_sheet(tmp_path, cli):
    from openpyxl import Workbook
    path = tmp_path / "formula.xlsx"
    book = Workbook()
    book.active.append(["amount"])
    book.active.append(["=1+1"])
    book.save(path)
    assert cli("inspect_table", path, expected=3)["error"]["code"] == "EXCEL_READ_ERROR"
    assert cli("inspect_table", path, "--sheet", "Missing", expected=2)["error"]["code"] == "SHEET_NOT_FOUND"


def test_json_argument_errors(cli, fixtures):
    result = cli("inspect_table", fixtures / "sales.csv", "--sample", "bad", expected=2)
    assert result["error"]["code"] == "INVALID_ARGUMENT"


@pytest.mark.parametrize("command", list(COMMANDS))
def test_all_help(command):
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{command}.py"), "--help"],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert not result.stderr
