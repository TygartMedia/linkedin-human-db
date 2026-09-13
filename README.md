# humandb — your LinkedIn connections are a human database

Here's the idea, plain as I can say it.

You've got a LinkedIn network. Maybe it's 500 people, maybe it's 5,000. It's messy — old coworkers, that guy from the conference, your cousin's business partner, three recruiters you never called back. It looks like a junk drawer.

It's not a junk drawer. It's the most valuable thing you own.

Every one of those people is good at something. One of them can run your calendar. One of them knows everybody in your town. One of them can get you on a podcast. You already did the hard part — you met them, you connected, they said yes. What's missing is the map: *what is each person good for, and where are my gaps?*

That's what this does. You download your own LinkedIn data (the official export — takes two minutes, LinkedIn emails you a zip), and this turns it into a capability database. Each contact gets tagged with what they're good for, ranked against what you're looking for, and you get a report that says: here's what you've got, here's who's most relevant, here's what you're missing.

Think of each contact as a human agent with capabilities. Because that's what they are.

## Why it's free

Because I want the best version of this to exist, and I'm one guy. If I keep it closed, it stays as good as I can make it on weekends. If I give it away, somebody smarter than me builds the thing I actually want — and then I get to use *that*.

So here it is. MIT licensed. Take it.

**Take this, make it better. If you build something better than this, come back — we'll be customer #1 and we'll pay you for it.**

That's the whole business model. I mean it.

## The one rule

This tool processes **only** LinkedIn's official data export — the GDPR/CCPA zip you request from LinkedIn yourself, about yourself. It will refuse anything else, on purpose.

No scraping. Not a little, not "just this once." Scraping other people's data is how you get banned and how you become the villain. Your export is your data; LinkedIn gives it to you; we work with that. If what you hand it doesn't look like the official export, it says no and tells you why.

## Quickstart

Requirements: Python 3.10+, and `pyyaml` (`pip install pyyaml`).

```bash
# 1. Get your export: LinkedIn → Settings → Data privacy → Get a copy of your data
#    (ask for the larger archive; LinkedIn emails you a zip, usually within a day)

# 2. Run the whole pipeline
python -m humandb run --export ~/Downloads/linkedin-export.zip --out ./my-network

# 3. Read your report
cat ./my-network/summary.md
```

You'll get three files in `./my-network`:

- `contacts.json` — every contact, enriched with capability tags and scores
- `contacts.csv` — the same, spreadsheet-friendly
- `summary.md` — counts, top capabilities, top-ranked contacts, and your coverage gaps

Re-exports merge cleanly — run it again next quarter with `--prev`:

```bash
python -m humandb run --export ~/Downloads/linkedin-export-2.zip --out ./my-network --prev ./my-network/contacts.json
```

It matches on profile URL first, falls back to name + company, and fills in blanks instead of duplicating people.

### Just curious? Try the demo

```bash
python -m humandb run --export sample_data/sample-linkedin-export.zip --out /tmp/demo
cat /tmp/demo/summary.md
```

All fake data. See `sample_data/README.md`.

### Individual stages

`run` does everything, but you can also go stage by stage:

```bash
python -m humandb parse   --export in.zip --out parsed.json
python -m humandb dedupe  --input parsed.json --prev old-contacts.json --out merged.json
python -m humandb analyze --input merged.json --out tagged.json [--config config.yaml]
python -m humandb score   --input tagged.json --out scored.json [--config config.yaml]
python -m humandb report  --input scored.json --out ./my-network [--config config.yaml]
```

## Configuration

Copy `config.yaml` and make it yours. Three things matter:

**1. `wishlist` — what you're hunting for right now.** Capability → weight. If you need a VA this quarter, weight `admin` at 3 and everything else at 1. Change it when your needs change; the ranking follows.

```yaml
wishlist:
  admin: 3
  operations: 2
  outreach: 2
```

**2. `capabilities` — what each capability means.** Keyword lists, matched against job titles and company names. Add your own; naming a capability replaces its keyword list, and anything you don't name keeps its default:

```yaml
capabilities:
  drone_pilot:
    - "drone pilot"
    - "UAV operator"
    - "Part 107"
```

The defaults cover: `admin`, `operations`, `outreach`, `sales`, `events`, `local_services`, `hiring`, `press`, `technical`, `creative`. Every tag carries its evidence — which keyword matched, in which field — so you can see *why* someone got tagged and fix the keywords when they're wrong. They will be wrong sometimes. That's why the evidence is there.

**3. `score_weights` — how the ranking blends.** Must sum to 1:

- `capability_fit` (0.6) — how well they match your wishlist
- `profile_completeness` (0.2) — how much info the export actually had
- `recency` (0.2) — newer connections score higher; tune with `recency_full_days` / `recency_zero_days`

Every contact keeps its score breakdown, so the ranking is explainable, not magic.

## The LLM plug-in point (v1 leaves this open on purpose)

The keyword tagger is deliberately dumb and transparent — v1's job is to work offline with zero API keys. But there's a clean seam for a smarter pass: see `humandb/llm_plugin.py`. Implement the `CapabilityEnricher` interface, plug it in between analyze and score, and an LLM can refine tags or draft outreach notes.

Two house rules for implementations, documented in the module: never commit API keys (env vars at runtime), and never silently replace the keyword tags — the transparent layer stays visible underneath.

## What v1 doesn't do (yet)

- No outreach automation. This maps the network; it doesn't message anyone. (Deliberate — the "love on them" part is human.)
- No web UI. CLI and files. Somebody's weekend project is waiting.
- No incremental LinkedIn sync — re-export and merge with `--prev`.
- English keyword defaults. The config makes other languages easy; nobody's done it yet.

## Tests

```bash
python -m unittest discover -s tests
```

22 tests, all on synthetic data (`tests/synthetic.py`). No real contact data anywhere in this repo, ever — the `.gitignore` refuses exports and outputs.

## The invitation, once more

This is v1. It's rough in the way first versions are. The keyword lists are my best guess, the scoring is simple on purpose, and there's a long list of things it doesn't do yet.

If you take this and make it sing — better tagging, a real UI, the LLM layer, integrations I haven't thought of — come back and tell me. **We'll be customer #1, and we'll pay you for it.**

— Will
