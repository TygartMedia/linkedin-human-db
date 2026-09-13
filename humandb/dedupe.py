"""Merge a fresh parse against a previous run's output.

Identity: profile URL first (normalized), falling back to normalized
name+company. When two records match, fields are unioned — blanks get filled
from whichever side has the value. Nothing is ever silently dropped; the
merge reports counts.
"""

import re


def _norm_key(value):
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def identity_key(record):
    """Primary identity: URL, else name+company fallback. Returns (key, method)."""
    if record.get("url"):
        return ("url:" + record["url"], "url")
    name = _norm_key(record.get("name"))
    company = _norm_key(record.get("company"))
    return (f"name:{name}|company:{company}", "name_company")


def merge_records(previous, fresh):
    """Merge fresh records into previous. Returns (merged_list, stats).

    stats: {"kept": n, "added": n, "enriched": n} where "enriched" counts
    previous records that gained at least one new field value.
    """
    merged = [dict(r) for r in previous]
    index = {}
    for rec in merged:
        key, _ = identity_key(rec)
        index[key] = rec
    stats = {"kept": len(previous), "added": 0, "enriched": 0}

    for rec in fresh:
        key, _ = identity_key(rec)
        if key in index:
            existing = index[key]
            enriched = False
            for field, value in rec.items():
                if value and not existing.get(field):
                    existing[field] = value
                    enriched = True
            if enriched:
                stats["enriched"] += 1
        else:
            new_rec = dict(rec)
            index[key] = new_rec
            merged.append(new_rec)
            stats["added"] += 1

    return merged, stats


def load_previous(path):
    """Load a previous run's enriched JSON. Returns [] if path is None."""
    if path is None:
        return []
    import json

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "contacts" in data:
        return data["contacts"]
    return data
