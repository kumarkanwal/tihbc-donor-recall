"""Tests for CSV and XLSX donor upload parsing."""

from io import BytesIO

import pytest
from openpyxl import Workbook

from app.core.errors import UploadInvalidError
from app.services.batch_upload.parser import parse_upload


def test_csv_headers_are_normalized() -> None:
    content = (
        b" Name ,Phone,Segment,LANGUAGE, Blood Group ,Last Donation Date\n"
        b" Ahsan Khan,0300-1234567,regular,English,O+,2026-01-15\n"
    )

    parsed = parse_upload("donors.CSV", content, max_size_mb=1, max_rows=10)

    assert parsed.original_filename == "donors.CSV"
    assert parsed.rows[0].row_number == 2
    assert parsed.rows[0].values["blood_group"] == "O+"
    assert parsed.rows[0].values["last_donation_date"] == "2026-01-15"


def test_xlsx_is_parsed() -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["name", "phone", "segment", "language"])
    sheet.append(["Fatima Ahmed", "+92 301 2345678", "Lapsed", "Urdu"])
    content = BytesIO()
    workbook.save(content)

    parsed = parse_upload("donors.xlsx", content.getvalue(), max_size_mb=1, max_rows=10)

    assert parsed.rows[0].values["name"] == "Fatima Ahmed"
    assert parsed.rows[0].values["language"] == "Urdu"


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("donors.txt", b"name,phone,segment,language", "Only CSV and XLSX"),
        ("donors.csv", b"", "empty"),
        ("donors.csv", b"name,phone\nAhsan,03001234567", "missing required"),
        ("donors.csv", b"name,phone,segment,language\n", "no donor rows"),
    ],
)
def test_invalid_file_shapes_are_rejected(filename: str, content: bytes, message: str) -> None:
    with pytest.raises(UploadInvalidError, match=message):
        parse_upload(filename, content, max_size_mb=1, max_rows=10)


def test_size_and_row_limits_are_enforced() -> None:
    with pytest.raises(UploadInvalidError, match="exceeds 1 MB"):
        parse_upload("donors.csv", b"x" * (1024 * 1024 + 1), max_size_mb=1, max_rows=10)

    content = (
        b"name,phone,segment,language\nOne,03001234567,regular,en\nTwo,03011234567,lapsed,ur\n"
    )
    with pytest.raises(UploadInvalidError, match="exceeds 1 rows"):
        parse_upload("donors.csv", content, max_size_mb=1, max_rows=1)


def test_duplicate_normalized_headers_are_rejected() -> None:
    content = (
        b"name,phone,segment,language,blood group,blood_group\nAhsan,03001234567,regular,en,O+,O+\n"
    )

    with pytest.raises(UploadInvalidError, match="duplicate columns"):
        parse_upload("donors.csv", content, max_size_mb=1, max_rows=10)
