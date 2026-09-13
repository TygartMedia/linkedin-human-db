"""Tag contacts with capability signals.

The built-in tagger is transparent keyword matching over the configured
search fields (default: position + company). Every tag carries its evidence:
which keyword matched, and in which field. No black boxes.

Want an LLM pass? See llm_plugin.py — implement the CapabilityEnricher
interface and plug it in. The keyword tags always run first and stay visible,
so an LLM can refine but never silently replace them.
"""

import re


def _compile(capabilities):
    """Compile keyword lists to regexes with word-ish boundaries.

    Multi-word phrases match as substrings; single tokens match on word
    boundaries so 'IT' doesn't match 'waiting'.
    """
    compiled = {}
    for cap, keywords in capabilities.items():
        patterns = []
        for kw in keywords:
            kw = kw.strip()
            if not kw:
                continue
            if " " in kw:
                patterns.append(re.compile(re.escape(kw), re.IGNORECASE))
            else:
                patterns.append(
                    re.compile(r"\b" + re.escape(kw) + r"s?\b", re.IGNORECASE)
                )
        compiled[cap] = patterns
    return compiled


def tag_inner_circle(records, names):
    """Tag the owner's warm core by exact name match.

    These are people the owner knows personally. The standing rule:
    outsourced finders/outreach never touch the inner circle — it is
    Will's to work directly. Matching is on the normalized full name.
    """
    wanted = {n.strip().lower() for n in (names or []) if n.strip()}
    count = 0
    for rec in records:
        if rec.get("name", "").strip().lower() in wanted:
            if "inner" not in rec["capabilities"]:
                rec["capabilities"].append("inner")
                rec["capabilities"].sort()
            rec.setdefault("capability_evidence", {})["inner"] = [
                "inner_circle~owner list"
            ]
            count += 1
    return count


def tag_records(records, capabilities, search_fields):
    """Add 'capabilities' (list) and 'capability_evidence' (dict) to each record."""
    compiled = _compile(capabilities)
    for rec in records:
        tags = []
        evidence = {}
        haystacks = {f: rec.get(f) or "" for f in search_fields}
        for cap, patterns in compiled.items():
            hits = []
            for pat in patterns:
                for field, text in haystacks.items():
                    m = pat.search(text)
                    if m:
                        hits.append(f"{field}~{m.group(0)!r}")
                        break
            if hits:
                tags.append(cap)
                evidence[cap] = hits
        # Subsumption: every franchise brand in the list is a restoration
        # company, so a franchise tag implies the trade tag even when the
        # company name doesn't literally say "restoration".
        if "restoration_franchise" in tags and "local_services" not in tags:
            tags.append("local_services")
            evidence["local_services"] = ["subsumed~restoration_franchise"]
        rec["capabilities"] = sorted(tags)
        rec["capability_evidence"] = evidence
    return records
