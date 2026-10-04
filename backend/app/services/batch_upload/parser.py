"""Parse donor CSV and XLSX uploads into normalized string rows."""

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import cast
from zipfile import BadZipFile

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException

from app.core.errors import UploadInvalidError

REQUIRED_COLUMNS = frozenset({"name", "phone", "segment", "language"})
OPTIONAL_COLUMNS = frozenset({"city", "blood_group", "last_donation_date"})
SUPPORTED_SUFFIXES = frozenset({".csv", ".xlsx"})
HEADER_SEPARATOR_PATTERN = re.compile(r"[\s_]+")
BYTES_PER_MEBIBYTE = 1024 * 1024


@dataclass(frozen=True)
class ParsedRow:
    """One upload row with its source-file row number."""

    row_number: int
    values: dict[str, str]


@dataclass(frozen=True)
class ParsedUpload:
    """A parsed upload ready for field-level validation."""

    original_filename: str
    rows: tuple[ParsedRow, ...]


def normalize_header(header: object) -> str:
    """Normalize header case and separators to snake case."""
    return HEADER_SEPARATOR_PATTERN.sub("_", str(header).strip().lower())


def parse_upload(
    filename: str,
    content: bytes,
    *,
    max_size_mb: int,
    max_rows: int,
) -> ParsedUpload:
    """Validate upload-level limits and parse CSV/XLSX data."""
    safe_filename = Path(filename).name
    suffix = Path(safe_filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UploadInvalidError("Only CSV and XLSX files are supported")
    if not content:
        raise UploadInvalidError("The uploaded file is empty")
    if len(content) > max_size_mb * BYTES_PER_MEBIBYTE:
        raise UploadInvalidError(f"The uploaded file exceeds {max_size_mb} MB")

    frame = _read_frame(content, suffix)
    normalized_columns = [normalize_header(column) for column in frame.columns]
    if len(set(normalized_columns)) != len(normalized_columns):
        raise UploadInvalidError("The uploaded file has duplicate columns")
    missing = sorted(REQUIRED_COLUMNS.difference(normalized_columns))
    if missing:
        raise UploadInvalidError(
            "The uploaded file is missing required columns",
            details={"missing_columns": missing},
        )
    if frame.empty:
        raise UploadInvalidError("The uploaded file contains no donor rows")
    if len(frame.index) > max_rows:
        raise UploadInvalidError(f"The uploaded file exceeds {max_rows} rows")

    frame.columns = normalized_columns
    frame = frame.fillna("")
    raw_records = cast(list[dict[str, object]], frame.to_dict(orient="records"))
    allowed_columns = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
    rows = tuple(
        ParsedRow(
            row_number=row_number,
            values={column: str(record.get(column, "")).strip() for column in allowed_columns},
        )
        for row_number, record in enumerate(raw_records, start=2)
    )
    return ParsedUpload(original_filename=safe_filename, rows=rows)


def _read_frame(content: bytes, suffix: str) -> pd.DataFrame:
    try:
        if suffix == ".csv":
            return pd.read_csv(BytesIO(content), dtype=str, keep_default_na=False)
        return pd.read_excel(
            BytesIO(content),
            dtype=str,
            keep_default_na=False,
            engine="openpyxl",
        )
    except (
        BadZipFile,
        InvalidFileException,
        OSError,
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ) as error:
        raise UploadInvalidError("The uploaded file could not be parsed") from error
