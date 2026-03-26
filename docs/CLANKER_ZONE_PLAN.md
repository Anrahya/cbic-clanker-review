# Clanker Zone Plan

`clanker zone` is a modular multi-agent review council for structured-document QA.
GST rule review is the first domain pack, not the permanent scope boundary.

## Stage 1. Constitution and Boundaries

Deliverables:

- shared council mission
- evidence hierarchy
- domain/plugin boundaries
- common judgment schema

Decisions already fixed:

- `clanker_core` must be reusable outside GST
- GST-specific logic belongs in `clanker_zone.domains.gst`
- MiniMax integration belongs in `clanker_zone.provider`
- live model execution is not required until the dossier model and pipeline are stable

## Stage 2. Dossier Model

Deliverables:

- rule dossiers
- parent-cluster dossiers
- amendment dossiers
- table dossiers

Inputs for GST:

- extracted rule JSON
- rule schema
- raw HTML
- hint JSON

Outputs:

- compact evidence packs that specialist counsel can review without reading the whole corpus

Current GST decision:

- the default reasoning unit is a parent structural cluster, usually one sub-rule with attached clauses, provisos, and explanations
- leaf nodes remain the reporting unit through target cards inside the cluster dossier
- this replaces isolated-node-first review because CBIC amendment and bracket scope often crosses sibling nodes

## Stage 3. Core Council Runtime

Deliverables:

- stage abstractions
- counsel roster model
- task planning
- arbitration model
- judgment aggregation contract

Initial stages:

1. docket
2. specialist review
3. skepticism/challenge
4. arbitration
5. reporting

## Stage 4. GST Domain Pack

Deliverables:

- corpus discovery for the `pc/` data layout
- GST policy and category registry
- GST-specific dossier builders
- GST specialist prompt registry

The GST pack must understand:

- source blocks
- segments
- amendment spans
- table hints
- schema allowances for structural nodes

## Stage 5. MiniMax Provider

Deliverables:

- MiniMax M2.7 provider config
- Anthropic-compatible request builder
- prompt caching-aware shared prompt prefix
- API key resolution and guard rails

Constraint:

- ask for the API key only when live provider execution is the next blocking step

## Stage 6. Local Validation

Deliverables:

- corpus-discovery tests
- dossier-construction tests
- council-planning tests
- provider-payload tests

No live model calls in this stage.

## Stage 7. Live Council Runs

Blocked on:

- MiniMax API key

Deliverables after key is provided:

- one real council run on a GST rule
- prompt tuning based on observed outputs
- final report rendering and retry policy tuning

## Stage 8. Issue-Centric Deliberation

Deliverables:

- candidate issue graph aggregated from specialist judgments
- issue-by-issue skeptic review
- issue-by-issue arbiter review
- rule-level synthesis report

Decisions already fixed:

- specialists review dossiers
- skeptics and arbiters review candidate issues, not raw dossiers alone
- every issue stage prompt must include the dossier, the normalized candidate issue, and the prior judgments that led to it
- final rule status is derived from arbiter outcomes, with skeptic outcomes as fallback only

## Stage 9. Full GST Review Command

Deliverables:

- `clanker-zone gst-review`
- persisted artifacts for:
  - specialist requests/results
  - candidate issues
  - challenge requests/results
  - arbiter requests/results
  - synthesized rule report

This is the first end-to-end council path for whole-rule GST review.

## Stage 10. Parent-Cluster Review Units

Deliverables:

- GST dossier builder defaults to parent structural clusters, usually one sub-rule at a time
- cluster dossiers include:
  - cluster root fragment
  - target cards for each child node
  - full source block span
  - overlapping amendment spans
  - overlapping hint segments
- leaf node ids remain the reporting unit even when the reasoning unit is the cluster

This stage exists because CBIC source structure often spans sibling provisos or clauses, so isolated node review over-flags bracket carryover and amendment-scope artifacts.

## Current Runtime Shape

Defined council roles:

1. `docket_clerk`
2. `source_fidelity_counsel`
3. `structure_scope_counsel`
4. `amendment_counsel`
5. `reference_counsel`
6. `table_counsel`
7. `artifact_defender`
8. `chief_arbiter`

Current GST live review path uses:

- `5` specialist roles
- `1` skeptic role
- `1` arbiter role

`docket_clerk` is currently architectural only and not a separate live provider call.
