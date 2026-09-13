"""Optional LLM enrichment — interface only. Nothing here makes network
calls, holds API keys, or depends on any vendor.

To add an LLM pass:
    1. Implement CapabilityEnricher.enrich(records, capabilities) in your own
       module. It receives the keyword-tagged records and returns records
       (mutated or new). Suggested use: refine tags, add a 'notes' field,
       propose capabilities the keywords missed.
    2. Pass your enricher to run_pipeline(..., enricher=...) or call it
       between the analyze and score stages yourself.

Rules for implementations (enforced by convention, documented here):
- Never commit API keys. Read them from the environment at runtime.
- Never silently replace keyword tags. Add to them, or put LLM-only tags in
- Never send more personal data than the task needs; these are the user's
  own contacts, but minimization still applies.
"""

from typing import Dict, List


class CapabilityEnricher:
    """Interface for an optional LLM (or other) enrichment pass."""

    name = "base"

    def enrich(
        self, records: List[Dict], capabilities: Dict[str, List[str]]
    ) -> List[Dict]:
        """Enrich keyword-tagged records. Return the records to continue the pipeline."""
        raise NotImplementedError


class NoOpEnricher(CapabilityEnricher):
    """Default: changes nothing. The pipeline runs fully offline."""

    name = "none"

    def enrich(self, records, capabilities):
        return records
