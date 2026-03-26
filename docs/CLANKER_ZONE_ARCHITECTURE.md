# Clanker Zone Architecture

## Goal

Build a reusable council that judges structured outputs against schema and source evidence.

## Layers

### `clanker_core`

- dossier contracts
- judgments
- task planning
- stage orchestration
- arbitration

### `clanker_domain_*`

Each domain pack contributes:

- policy
- categories
- dossier builders
- prompt registry
- artifact tolerances

### `clanker_provider_*`

Each provider contributes:

- request payload builder
- auth resolution
- message normalization
- response normalization

## Evidence Hierarchy

1. raw source meaning
2. structured source evidence
3. schema constraints
4. candidate output

## Council Pattern

1. `docket_clerk`
2. specialist counsel
3. candidate issue aggregation
4. `artifact_defender`
5. `chief_arbiter`
6. rule synthesis

## Deliberation Flow

1. build dossiers from extracted JSON, schema, raw HTML, and hint JSON
2. for GST, prefer parent-cluster dossiers such as one sub-rule with all attached clauses/provisos/explanations
3. run specialist counsel over those cluster dossiers
4. attribute every issue back to the exact target node inside the cluster
5. aggregate `confirmed_issue` judgments into a deduplicated candidate issue graph
6. run `artifact_defender` over each candidate issue with the originating judgments attached
7. run `chief_arbiter` over each candidate issue with both specialist and skeptic judgments attached
8. synthesize a rule-level report from the arbiter outcomes

This keeps direct agent-to-agent chat out of the system. The shared medium is structured artifacts:

- dossiers
- candidate issues
- judgments
- synthesized reports

## GST-Specific Notes

The current GST corpus has:

- block-based source spans
- bracketed amendment scopes across multiple blocks
- top-level amendment events
- cross-reference hints
- table hints with header/body structure
- omitted-yet-modeled provisos and clauses

That means GST dossiers should prefer hint-derived evidence and use raw HTML as secondary tie-break evidence.

The current GST workflow entry point is `clanker-zone gst-review`, which persists every intermediate artifact for auditability.
