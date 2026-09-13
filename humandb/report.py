"""Emit the outputs: enriched JSON, enriched CSV, and a markdown summary.

The summary answers three questions at a glance:
1. What do I have? (counts, top capabilities)
2. Who's most relevant? (top-N by score)
3. What am I missing? (wishlist capabilities with thin or zero coverage)
"""

import csv
import json
import os

CSV_COLUMNS = [
    "name", "position", "company", "location", "email", "url",
    "connected_on", "capabilities", "score",
]


def write_outputs(records, config, outdir, stats=None):
    """Write contacts.json, contacts.csv, summary.md into outdir. Returns paths."""
    os.makedirs(outdir, exist_ok=True)
    stats = stats or {}

    json_path = os.path.join(outdir, "contacts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {"meta": {"count": len(records), "merge_stats": stats}, "contacts": records},
            f, indent=1, ensure_ascii=False,
        )

    csv_path = os.path.join(outdir, "contacts.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in records:
            w.writerow(
                {
                    "name": r.get("name", ""),
                    "position": r.get("position", ""),
                    "company": r.get("company", ""),
                    "location": r.get("location", ""),
                    "email": r.get("email", ""),
                    "url": r.get("url", ""),
                    "connected_on": r.get("connected_on", ""),
                    "capabilities": ", ".join(r.get("capabilities", [])),
                    "score": r.get("score", ""),
                }
            )

    md_path = os.path.join(outdir, "summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_summary(records, config, stats))

    return {"json": json_path, "csv": csv_path, "summary": md_path}


def build_summary(records, config, stats):
    total = len(records)
    cap_counts = {}
    for r in records:
        for cap in r.get("capabilities", []):
            cap_counts[cap] = cap_counts.get(cap, 0) + 1
    ranked_caps = sorted(cap_counts.items(), key=lambda kv: kv[1], reverse=True)

    wishlist = config.get("wishlist", {})
    gaps = [
        (cap, cap_counts.get(cap, 0))
        for cap in wishlist
        if cap_counts.get(cap, 0) < 3
    ]
    gaps.sort(key=lambda kv: kv[1])

    top_n = config.get("report_top_n", 20)
    lines = [
        "# Human Database — summary",
        "",
        f"**Contacts:** {total}",
    ]
    if stats:
        lines.append(
            "**Merge:** kept {kept}, added {added}, enriched {enriched}".format(**stats)
        )
    lines += ["", "## Top capabilities", ""]
    if ranked_caps:
        for cap, n in ranked_caps[:15]:
            lines.append(f"- {cap}: {n}")
    else:
        lines.append("- (no capability tags matched — check your config)")
    lines += ["", f"## Top {top_n} by score", ""]
    for r in records[:top_n]:
        caps = ", ".join(r.get("capabilities", [])) or "—"
        lines.append(
            f"- **{r.get('name', '?')}** — {r.get('position', '?')} @ "
            f"{r.get('company', '?')} (score {r.get('score', '?')}, {caps})"
        )
    lines += ["", "## Coverage gaps", ""]
    if gaps:
        lines.append("Wishlist capabilities with fewer than 3 contacts:")
        for cap, n in gaps:
            lines.append(f"- {cap}: {n} contact(s) — worth finding more of these")
    else:
        lines.append("No gaps — every wishlist capability has 3+ contacts.")
    lines.append("")
    return "\n".join(lines)
