"""Generate the donor batch sample CSV."""

import csv
from io import StringIO

SAMPLE_FILENAME = "tihbc-donor-batch-sample.csv"
SAMPLE_HEADERS = (
    "name",
    "phone",
    "segment",
    "language",
    "city",
    "blood_group",
    "last_donation_date",
)
SAMPLE_ROWS = (
    ("Ahsan Khan", "0300-1234567", "regular", "English", "Karachi", "O+", "2026-01-15"),
    ("Fatima Ahmed", "+92 301 2345678", "lapsed", "Urdu", "Lahore", "A+", "15/12/2025"),
    ("Bilal Ali", "923021234567", "first_time", "en", "Islamabad", "B-", ""),
)


def generate_sample_csv() -> bytes:
    """Return a UTF-8 CSV with the correct columns and three examples."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(SAMPLE_HEADERS)
    writer.writerows(SAMPLE_ROWS)
    return output.getvalue().encode("utf-8")
