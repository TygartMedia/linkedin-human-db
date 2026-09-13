"""Load and validate the YAML config. Applies defaults so a minimal
config.yaml works; a full example ships as config.yaml in the repo root."""

import copy

import yaml

DEFAULT_CAPABILITIES = {
    "admin": [
        "virtual assistant", "executive assistant", "office manager",
        "administrator", "administrative", "scheduler", "scheduling",
        "bookkeeper", "personal assistant",
    ],
    "operations": [
        "operations", "project manager", "program manager", "COO",
        "chief operating", "logistics", "supply chain", "process improvement",
    ],
    "outreach": [
        "outreach", "business development", "partnerships", "partner manager",
        "community manager", "evangelist", "developer relations",
    ],
    "sales": [
        "sales", "account executive", "SDR", "BDR", "account manager",
        "closer", "revenue", "business development rep",
    ],
    "events": [
        "event planner", "event manager", "events", "conference",
        "trade show", "wedding planner",
    ],
    "local_services": [
        "restoration", "plumber", "plumbing", "electrician", "contractor",
        "HVAC", "roofer", "roofing", "handyman", "cleaning service",
        "landscaper", "painter",
    ],
    "hiring": [
        "recruiter", "recruiting", "talent acquisition", "sourcer",
        "human resources", "staffing",
    ],
    "press": [
        "journalist", "reporter", "editor", "media", "public relations",
        "communications", "podcast host", "blogger",
    ],
    "technical": [
        "engineer", "developer", "software", "data scientist", "data analyst",
        "devops", "IT manager", "systems administrator", "architect",
    ],
    "creative": [
        "designer", "writer", "copywriter", "marketing", "content",
        "brand", "video", "photographer", "social media",
    ],
}

DEFAULT_CONFIG = {
    "capabilities": copy.deepcopy(DEFAULT_CAPABILITIES),
    # Fields searched for capability keywords, in order.
    "search_fields": ["position", "company"],
    # What you're looking for right now: capability -> weight (higher = matters more).
    "wishlist": {
        "admin": 3,
        "operations": 2,
        "outreach": 2,
        "local_services": 1,
    },
    # Blend for the final score. Must sum to 1.
    "score_weights": {
        "capability_fit": 0.6,
        "profile_completeness": 0.2,
        "recency": 0.2,
    },
    # Recency: full marks for connections newer than this many days, then linear decay.
    "recency_full_days": 365,
    "recency_zero_days": 3650,
    "report_top_n": 20,
}


def load(path):
    """Load config.yaml, merge over defaults, validate. Returns a dict."""
    with open(path, encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}
    cfg = default()
    _deep_merge(cfg, user)
    _validate(cfg)
    return cfg


def default():
    """A fresh copy of the built-in defaults (no config file needed)."""
    return copy.deepcopy(DEFAULT_CONFIG)


def _deep_merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _validate(cfg):
    weights = cfg["score_weights"]
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"score_weights must sum to 1.0, got {total}")
    if not cfg["capabilities"]:
        raise ValueError("capabilities must not be empty")
    if cfg["recency_zero_days"] <= cfg["recency_full_days"]:
        raise ValueError("recency_zero_days must exceed recency_full_days")
