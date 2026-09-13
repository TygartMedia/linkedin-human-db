"""Parse the official LinkedIn data export zip into normalized records.

Only the official export format is accepted. If the zip doesn't contain a
Connections.csv with LinkedIn's header, we refuse — this tool never scrapes
LinkedIn and never tries to be clever about other inputs.
"""

import csv
import re
import zipfile

# The header LinkedIn writes in its official Connections.csv export.
EXPECTED_HEADER = [
    "First Name",
    "Last Name",
    "URL",
    "Email Address",
    "Company",
    "Position",
    "Connected On",
]

# Some exports include a Location column; tolerate it, don't require it.
OPTIONAL_COLUMNS = {"Location"}


class NotAnOfficialExport(Exception):
    """Raised when the input doesn't look like LinkedIn's official export."""


def _norm_url(url):
    """Normalize a LinkedIn profile URL for identity matching."""
    url = (url or "").strip().lower()
    url = re.sub(r"[?#].*$", "", url)  # drop tracking params/fragments
    return url.rstrip("/")


def _norm_text(value):
    return (value or "").strip()


def parse_export(zip_path):
    """Read zip_path, return a list of normalized contact records.

    Each record: name, first, last, url, email, company, position,
    location, connected_on (raw string as LinkedIn wrote it).
    """
    with zipfile.ZipFile(zip_path) as z:
        csv_name = _find_connections_csv(z.namelist())
        if csv_name is None:
            raise NotAnOfficialExport(
                f"{zip_path} contains no Connections.csv — this doesn't look "
                "like LinkedIn's official data export. Download yours from "
                "LinkedIn Settings > Data privacy > Get a copy of your data."
            )
        with z.open(csv_name) as f:
            raw = f.read().decode("utf-8-sig", errors="replace").splitlines()

    reader = csv.DictReader(raw)
    _check_header(reader.fieldnames, zip_path)

    records = []
    for row in reader:
        if not any((v or "").strip() for v in row.values()):
            continue  # skip blank rows
        first = _norm_text(row.get("First Name"))
        last = _norm_text(row.get("Last Name"))
        records.append(
            {
                "name": f"{first} {last}".strip(),
                "first": first,
                "last": last,
                "url": _norm_url(row.get("URL")),
                "email": _norm_text(row.get("Email Address")),
                "company": _norm_text(row.get("Company")),
                "position": _norm_text(row.get("Position")),
                "location": _norm_text(row.get("Location")),
                "connected_on": _norm_text(row.get("Connected On")),
            }
        )
    return records


def _find_connections_csv(names):
    for n in names:
        if n.lower().endswith("connections.csv"):
            return n
    return None


def _check_header(fieldnames, zip_path):
    given = [h.strip() for h in (fieldnames or [])]
    missing = [h for h in EXPECTED_HEADER if h not in given]
    if missing:
        raise NotAnOfficialExport(
            f"{zip_path}: Connections.csv is missing expected columns "
            f"{missing} — refusing to guess. This tool only processes "
            "LinkedIn's official export format."
        )
