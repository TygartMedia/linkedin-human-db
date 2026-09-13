"""Rank contacts against the wishlist.

Three components, blended by score_weights from the config:
- capability_fit: weighted wishlist matches, normalized to 0..1
- profile_completeness: fraction of informative fields that are filled
- recency: 1.0 for fresh connections, decaying to 0.0 for old ones

Every component is stored on the record so the ranking stays explainable.
"""

from datetime import date, datetime

COMPLETENESS_FIELDS = ["position", "company", "email", "location", "url"]

# LinkedIn writes dates like "12 Jan 2020", "Jan 12, 2020", "2020-01-12", "01/12/2020".
DATE_FORMATS = ("%d %b %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")


def _parse_date(raw):
    raw = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def capability_fit(record, wishlist):
    """0..1 — weighted share of wishlist capabilities this contact has."""
    tags = set(record.get("capabilities") or [])
    total = sum(w for w in wishlist.values() if w > 0)
    if total <= 0:
        return 0.0
    hit = sum(w for cap, w in wishlist.items() if w > 0 and cap in tags)
    return round(hit / total, 4)


def completeness(record):
    """0..1 — share of informative fields that are non-empty."""
    filled = sum(1 for f in COMPLETENESS_FIELDS if (record.get(f) or "").strip())
    return round(filled / len(COMPLETENESS_FIELDS), 4)


def recency(record, full_days, zero_days, today=None):
    """0..1 — 1.0 within full_days, linear decay to 0.0 at zero_days.

    Unparseable/missing dates score 0.5: unknown, not bad.
    """
    today = today or date.today()
    d = _parse_date(record.get("connected_on"))
    if d is None:
        return 0.5
    age = max(0, (today - d).days)
    if age <= full_days:
        return 1.0
    if age >= zero_days:
        return 0.0
    return round(1.0 - (age - full_days) / (zero_days - full_days), 4)


def score_records(records, config, today=None):
    """Add score components + total, sort descending. Returns the sorted list."""
    weights = config["score_weights"]
    wishlist = config.get("wishlist", {})
    full_days = config["recency_full_days"]
    zero_days = config["recency_zero_days"]
    for rec in records:
        fit = capability_fit(rec, wishlist)
        comp = completeness(rec)
        recn = recency(rec, full_days, zero_days, today=today)
        total = (
            weights["capability_fit"] * fit
            + weights["profile_completeness"] * comp
            + weights["recency"] * recn
        )
        rec["score_breakdown"] = {
            "capability_fit": fit,
            "profile_completeness": comp,
            "recency": recn,
        }
        rec["score"] = round(total, 4)
    records.sort(key=lambda r: r["score"], reverse=True)
    return records
