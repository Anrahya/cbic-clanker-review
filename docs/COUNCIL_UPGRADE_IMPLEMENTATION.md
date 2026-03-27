# Council Upgrade Implementation Plan

## Goal

Improve the GST review council so it is:

- more precise on real extraction defects
- less vulnerable to policy/schema false positives
- robust against stale artifact review
- efficient enough to use MiniMax M2.7 well within the current budget

Current working budget:

- `1500` MiniMax requests per `5` hours

This is enough for a strong multi-agent review system, but only if requests are routed selectively and each stage has a tight contract.

---

## Current Strengths

The current council already has the right high-level shape:

- dossier-driven review
- specialist roles
- issue aggregation
- skeptic challenge
- arbiter finalization
- persisted artifacts

The current GST live review path is already better than a single freeform review prompt because it:

- reasons from structured evidence
- separates review roles
- preserves audit artifacts
- has a false-positive filter after arbitration

---

## Current Failure Modes

The main remaining problems are not architectural. They are decision-contract problems.

### 1. Amendment event date vs node-version date confusion

Observed in rules like:

- `R21-b`
- `R22(3)`

Pattern:

- one amendment has explicit `effective_date`
- a later amendment also contributes to the current node text
- the later amendment has only `enacted_date`
- the council still wants to backfill node `effective_from` from the earlier explicit date

Why this is wrong:

- `node.effective_from` means when the **current node version** became effective
- it is not the same as "the earliest amendment affecting this node that has a date"

### 2. Extraction defect vs policy/schema disagreement confusion

Observed in findings about:

- textless structural wrappers
- node status vs pending inline amendment
- source_ref anchor preview behavior
- target text vs target_id expectations

Pattern:

- reviewer sees a representation choice
- reviewer treats it as an extraction bug

### 3. Stale artifact review

Observed multiple times in rule review iterations.

Pattern:

- reviewer evaluates an older uploaded JSON
- finding is valid for a prior artifact, not the current one

### 4. Too much trust in heuristic signals

Pattern:

- a deterministic signal says "missing effective_from"
- a specialist confirms it without testing whether the current node version actually supports that claim

### 5. Full specialist fan-out on dossiers that do not need it

Pattern:

- all specialists run even when the dossier clearly has no tables, no complex amendments, or no structure risk

Result:

- wasted MiniMax budget
- more low-signal output
- more arbitration load

---

## Design Principles

### Principle 1: Preserve deterministic hard gates

The council should not replace all deterministic validation.

Keep these as hard gates:

- schema validity
- artifact freshness
- id/full_path/order integrity
- impossible or contradictory structural states
- impossible chronology states
- missing source URL consistency

The council should interpret semantic questions, not decide whether basic invariants still exist.

### Principle 2: Treat deterministic checks as signals, not verdicts

Deterministic findings should seed review, but not dictate it.

Example:

- `CHRON-EFFECTIVE-MISSING` is a signal
- the model must still decide whether it is a real extraction defect or an acceptable artifact

### Principle 3: Distinguish node-version chronology from amendment-event chronology

This needs to become a first-class council rule.

Rule:

- An amendment event can have an explicit `effective_date`
- but a node should only get `effective_from` if the **current node version** is fully supported by explicit commencement/effective evidence

If current node text depends on a later non-omitted amendment that has only `enacted_date`, then:

- do not require node `effective_from`
- classify "missing effective_from" as acceptable artifact or no issue

### Principle 4: Freshness must be visible in the dossier

Every dossier should carry enough metadata to detect stale-review risk:

- absolute rule JSON path
- rule JSON modified timestamp
- rule JSON content hash
- raw HTML path and hash
- hint JSON path and hash
- session timestamp

### Principle 5: Use MiniMax for bounded reasoning, not giant prompts

MiniMax M2.7 should be used for:

- specialist review on compact dossiers
- issue-level skepticism
- issue-level arbitration
- manual-review summarization

Not for:

- giant whole-rule freeform review
- redoing deterministic checks the code can already do

---

## Target Runtime Shape

## Stage A: Deterministic Review Signals

Keep and extend the existing deterministic review pipeline in `gst_rule_review`.

Output should be:

- hard invariant failures
- heuristic signals

Hard failures stop or downgrade review confidence.

Heuristic signals feed the council.

### Hard-gate classes

- schema invalid
- missing source URL consistency
- bad path/id/order
- stale artifact mismatch
- impossible source_ref geometry
- impossible chronology contradictions

### Heuristic signal classes

- possible chronology ambiguity
- possible cross-ref under-resolution
- possible duplicate refs
- possible source_ref truncation
- possible scope error

---

## Stage B: Live Docket Clerk

Make `docket_clerk` a real live stage.

Current docs mention it architecturally, but it is not executed live. That should change.

Responsibilities:

- summarize evidence scope
- identify likely risk families
- decide which specialists are needed
- flag policy-sensitive dossiers
- flag stale-review risk

Output contract:

- `recommended_specialists`
- `risk_summary`
- `policy_sensitive: true/false`
- `freshness_warning: true/false`
- `signal_priority`

This stage should be short and cheap.

---

## Stage C: Adaptive Specialist Routing

Do not run every specialist on every dossier.

Use the docket output plus deterministic signals to route specialists.

Suggested routing:

- `source_fidelity_counsel`
  - only if text/raw/source_ref signals exist
- `structure_scope_counsel`
  - only if children/provisos/explanations or scope signals exist
- `amendment_counsel`
  - only if amendment markers/events/chronology are present
- `reference_counsel`
  - only if cross_refs/source_refs/duplicate-ref signals exist
- `table_counsel`
  - only if table evidence exists

This is the highest-value request-budget improvement.

---

## Stage D: Signal-Backed Specialist Review

Specialists should not operate as unconstrained issue generators.

For each dossier, they should receive:

- dossier
- deterministic signals relevant to their category
- stage instructions

Specialists may:

- validate or reject seeded signals
- add at most `1` new unseeded issue when strongly supported

This keeps coverage while reducing hallucinated or noisy issue creation.

---

## Stage E: Skeptic and Arbiter at Issue Level

Keep the current issue-level challenge and arbitration model.

That is the right shape.

But strengthen the contracts:

### Skeptic should classify issues as one of:

- real extraction defect
- acceptable artifact
- policy/schema disagreement
- stale artifact risk
- insufficient evidence

### Arbiter should output one final disposition only:

- `confirmed_issue`
- `acceptable_artifact`
- `manual_review`
- `rejected`

No mixed semantics in final reporting.

---

## Stage F: Manual Review Summarizer

Add a final optional stage for `manual_review` items.

Purpose:

- tell a human exactly what to check on the CBIC page
- reduce vague review burden

Output format:

- target node
- exact source phrase to verify
- exact footnote to verify
- decision question

Example:

- "Does the current live text of clause `(b)` include wording from marker `2`?"
- "Does marker `2` contain explicit `w.e.f.` language or only notification `dated` language?"

This is cheap and high value.

---

## Prompt and Policy Changes

These are the highest-priority prompt upgrades.

### 1. Add node-version chronology doctrine

Files:

- `clanker_zone/domains/gst/policy.py`
- `clanker_zone/domains/gst/prompts.py`

Add this rule explicitly:

- distinguish amendment-event chronology from node-version chronology
- do not require node `effective_from` just because one affecting amendment has explicit `effective_date`
- if the current node text also depends on a later non-omitted amendment that lacks explicit `effective_date` or `commencement_date`, node `effective_from` may correctly remain null

This should be mentioned in:

- `gst.amendment`
- `gst.challenge_issue`
- `gst.arbitrate_issue`

### 2. Add stale artifact doctrine

Files:

- `clanker_zone/domains/gst/prompts.py`
- `clanker_zone/report/finalize.py`

Rule:

- if artifact freshness metadata suggests the report may be evaluating an older JSON than the current session artifact, downgrade to `manual_review` or `rejected`

### 3. Add policy-vs-defect doctrine

Files:

- `clanker_zone/domains/gst/prompts.py`
- `clanker_zone/domains/gst/false_positive_filter.py`

Rule:

- if the issue is really disagreement with schema semantics or extraction policy, it is not a confirmed extraction defect

---

## Dossier Changes

Files likely involved:

- `clanker_zone/dossier.py`
- `clanker_zone/domains/gst/...`

Add dossier metadata:

- `rule_json_path`
- `rule_json_mtime`
- `rule_json_sha256`
- `raw_html_path`
- `raw_html_sha256`
- `hint_json_path`
- `hint_json_sha256`
- `review_session_started_at`

These should be included in:

- dossier metadata
- persisted artifacts
- arbiter context

---

## Reporting Changes

Current reporting improved, but make it stricter.

Files likely involved:

- `clanker_zone/report/finalize.py`
- `clanker_zone/models.py`

Requirements:

- `final_disposition` is the only field used to bucket issues in final report
- `status` is derived only from final dispositions
- summary text is derived only from final dispositions
- no pre-final labels should drive status

---

## Request Budget Strategy

With `1500` requests per `5` hours, the council should be designed around selective fan-out.

### Recommended average budget per dossier

Clean/simple dossier:

- `1` docket
- `1-2` specialists
- `0-1` skeptic
- `0-1` arbiter

Target: `2-5` requests

Medium dossier:

- `1` docket
- `2-3` specialists
- `1-2` skeptic
- `1-2` arbiter

Target: `5-8` requests

Complex dossier:

- `1` docket
- `3-4` specialists
- `2-3` skeptic
- `2-3` arbiter

Target: `8-12` requests

### Anti-waste rules

- do not run `table_counsel` without table evidence
- do not run `amendment_counsel` on unamended dossiers
- do not arbitrate issues already downgraded to acceptable artifact by both skeptic and false-positive filter
- cap unseeded issues per specialist to `1`

---

## Recommended File-Level Implementation Order

### Phase 1: Policy and prompt correction

1. `clanker_zone/domains/gst/policy.py`
2. `clanker_zone/domains/gst/prompts.py`

Deliverables:

- chronology doctrine
- policy-vs-defect doctrine
- stale artifact doctrine

### Phase 2: Dossier freshness metadata

1. `clanker_zone/dossier.py`
2. GST dossier builders
3. persisted artifact serializers

Deliverables:

- hashes
- mtimes
- session timestamps

### Phase 3: Live docket clerk

1. `clanker_zone/stages/docket.py`
2. `clanker_zone/council.py`
3. `clanker_zone/workflow.py`

Deliverables:

- real docket calls
- specialist routing recommendations

### Phase 4: Adaptive specialist routing

1. `clanker_zone/stages/specialist.py`
2. `clanker_zone/council.py`

Deliverables:

- selected specialists per dossier
- lower average request count

### Phase 5: Final report hardening

1. `clanker_zone/report/finalize.py`
2. `clanker_zone/domains/gst/false_positive_filter.py`

Deliverables:

- final-disposition-only synthesis
- better downgrade logic

### Phase 6: Manual-review summarizer

1. add a new stage or post-report helper

Deliverables:

- concise human review instructions for manual-review issues

---

## Acceptance Criteria

The upgrade is successful when the council correctly handles these specific cases:

### Chronology

- `R21-b`
  - does **not** require `effective_from = 2017-06-22`
- `R22(3)`
  - does **not** require `effective_from = 2017-06-22`
- `R26(1)-P4`
  - does **not** require `effective_from = 2021-08-29`

### Policy vs defect

- textless structural wrappers are not flagged as defects when schema allows them
- active node with pending inline insertion is not auto-flagged as wrong status

### Freshness

- stale uploaded JSON vs fresh local JSON can be detected and downgraded

### Reporting

- no internal contradiction between:
  - `status`
  - `confirmed_issues`
  - `accepted_artifacts`
  - `manual_review_issues`
  - `final_disposition`

---

## Recommended Regression Corpus

Use at least these rules as recurring canaries:

- `R8`
- `R9`
- `R10B`
- `R19`
- `R21`
- `R22`
- `R26`

Why:

- these already exposed the core failure families:
  - chronology
  - source_ref precision
  - amendment target refinement
  - wrapper-node policy
  - cross-ref precision

---

## Bottom Line

The council does not need a new architecture.

It needs:

- stricter decision doctrine
- better dossier freshness evidence
- adaptive specialist routing
- stronger distinction between deterministic signals and final verdicts

MiniMax M2.7 is already good enough for this system if it is used for:

- compact specialist reasoning
- issue-level skepticism
- issue-level arbitration

and not wasted on unconditional full-fanout review of every dossier.
