"""Synthetic LinkedIn export generator for tests.

Every name, company, and email here is invented. This module exists so the
test suite and the README demo never touch real contact data.
"""

import csv
import io
import os
import tempfile
import zipfile

HEADER = [
    "First Name", "Last Name", "URL", "Email Address",
    "Company", "Position", "Connected On",
]

# (first, last, url, email, company, position, connected_on)
FAKE_CONTACTS = [
    ("Ava", "Rivera", "https://www.linkedin.com/in/ava-rivera-123",
     "ava@example.com", "Harbor Admin Co", "Virtual Assistant", "12 Jan 2024"),
    ("Ben", "Okafor", "https://www.linkedin.com/in/ben-okafor-456",
     "", "Northline Logistics", "Operations Manager", "03 Mar 2021"),
    ("Cara", "Nguyen", "https://www.linkedin.com/in/cara-nguyen-789",
     "cara@example.com", "Brightline Studio", "Event Planner", "22 Jun 2023"),
    ("Dev", "Patel", "https://www.linkedin.com/in/dev-patel-012",
     "dev@example.com", "Cascade Restoration", "Project Manager", "15 Sep 2019"),
    ("Erin", "Walsh", "https://www.linkedin.com/in/erin-walsh-345",
     "", "Signal & Co", "Recruiter", "08 Nov 2022"),
    ("Finn", "Gallagher", "https://www.linkedin.com/in/finn-gallagher-678",
     "finn@example.com", "Pixelforge", "Software Engineer", "30 Jan 2025"),
    ("Gia", "Rossi", "https://www.linkedin.com/in/gia-rossi-901",
     "", "Rossi Media", "Podcast Host", "14 Feb 2020"),
    ("Hugo", "Larsen", "https://www.linkedin.com/in/hugo-larsen-234",
     "hugo@example.com", "Larsen & Partners", "Account Executive", "05 May 2023"),
    ("Ivy", "Chen", "https://www.linkedin.com/in/ivy-chen-567",
     "", "Chen Design", "Graphic Designer", "19 Jul 2021"),
    ("Jonas", "Weber", "https://www.linkedin.com/in/jonas-weber-890",
     "jonas@example.com", "Weber Outreach", "Business Development Rep", "11 Dec 2024"),
    # Duplicate of Ava Rivera with a different URL shape + an email filled in —
    # dedupe should merge these on normalized URL.
    ("Ava", "Rivera", "https://www.linkedin.com/in/ava-rivera-123/",
     "ava.rivera@example.com", "Harbor Admin Co", "", "12 Jan 2024"),
    # Same name+company, no URL — exercises the name+company fallback.
    ("Sam", "Taylor", "",
     "", "Harbor Admin Co", "Office Manager", "01 Apr 2022"),
    ("Sam", "Taylor", "",
     "sam@example.com", "Harbor Admin Co", "Office Manager", "01 Apr 2022"),
    # Sparse record — low completeness.
    ("Noah", "Kim", "https://www.linkedin.com/in/noah-kim-111",
     "", "", "", ""),
    # Old connection — low recency.
    ("Olivia", "Brown", "https://www.linkedin.com/in/olivia-brown-222",
     "", "Brown Plumbing", "Plumber", "09 Aug 2012"),
]


def make_export_zip(path=None, contacts=FAKE_CONTACTS, header=HEADER, preamble=None):
    """Write a fake LinkedIn export zip. Returns the zip path.

    preamble: optional list of lines written before the header, mimicking
    LinkedIn's Basic-export Notes: block.
    """
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
    buf = io.StringIO()
    if preamble:
        for line in preamble:
            buf.write(line + "\n")
    writer = csv.writer(buf)
    writer.writerow(header)
    for c in contacts:
        writer.writerow(c)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Connections.csv", buf.getvalue())
    return path


def make_bad_zip(path=None):
    """A zip that is NOT a LinkedIn export (for refusal tests)."""
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("random.txt", "hello")
    return path
