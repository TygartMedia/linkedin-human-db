"""humandb — turn your LinkedIn data export into a capability database.

Your LinkedIn connections are a human database: every person is a "human
agent" with capabilities. This tool reads the official LinkedIn data export
(the GDPR/CCPA zip LinkedIn emails you — never scraped), tags each contact
with capability signals, scores them against what you're looking for, and
reports coverage gaps.

Pipeline: parse -> dedupe -> analyze -> score -> report
"""

__version__ = "0.1.0"
