# GST Rule Review

Deterministic review pipeline for extracted GST rule JSON against raw CBIC HTML and a JSON Schema.

This workspace also includes `clanker_zone`, a MiniMax-backed multi-agent review council for evidence-bounded GST verification.

## Features

- Parses raw CBIC HTML into ordered blocks, tables, footnotes, and amendment markers.
- Indexes extracted rule JSON into node, parent/child, marker, cross-reference, and source-ref lookups.
- Runs conservative deterministic checks for schema validity, text fidelity, structure, provisos, clauses, tables, amendment markers, source refs, cross refs, statuses, chronology, and duplication.
- Emits both `review_report.json` and `review_report.md`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## CLI

```bash
gst-rule-review review --rule rule_008.json --schema rule_document.json --raw raw_rule8.html
gst-rule-review review --rule rule_026.json --schema rule_document.json
gst-rule-review fetch-raw --source-url https://cbic-gst.gov.in/... --out raw.html
clanker-zone gst-plan --rule-number 26 --out-dir clanker_runs/plan
clanker-zone gst-run --rule-number 26 --target-id CGST-R26(1)-P4 --counsel-name amendment_counsel
clanker-zone gst-review --rule-number 26 --out-dir clanker_runs/review
```

## Library API

```python
from gst_rule_review import ReviewConfig, review_rule_files

report = review_rule_files(
    rule_path="rule_008.json",
    schema_path="rule_document.json",
    raw_path="raw_rule8.html",
    config=ReviewConfig(),
)
print(report.overall_verdict.status)
```

## Design Notes

- The reviewer is conservative: only evidence-backed defects are confirmed.
- Textless structural nodes are tolerated by default.
- Amendment and chronology findings rely on visible source footnotes and mapped block spans.
- The pipeline is modular so checks can be extended for sections, chapters, or batch review later.
- `clanker_zone` runs a staged council: specialist dossier review, candidate issue aggregation, skeptic challenge, arbiter review, and rule-level synthesis.
# cbic-clanker-review
