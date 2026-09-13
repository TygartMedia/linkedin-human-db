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
        rec["capabilities"] = sorted(tags)
        rec["capability_evidence"] = evidence
    return records
