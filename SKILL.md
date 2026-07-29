---
name: evidence-gate-build
description: >
  Build guide for the DataHub Organizational Reasoning hackathon project
  ("Evidence Gate"). Use this whenever implementing, extending, testing, or
  debugging any part of this repository — the API, DataHub discovery layer,
  validation, decision engine, remediation generator, write-back,
  invalidation watcher, or precedent retrieval. This is the authoritative
  spec: if code and this file disagree, this file wins and the code is wrong.
---

# Evidence Gate — Build & Verification Guide

You are implementing one concrete agent workflow against a real, running
DataHub instance. Read this whole file before writing code. Do not start a
milestone until the previous one's verification checklist passes for real,
observable reasons (actual DataHub UI state, actual test output) — not
because the code "looks right."

## Non-negotiable constraints

These override any convenience shortcut, at any point in the build:

1. **Never mock the graph in the demo path.** All lineage, ownership,
   glossary, policy, and quality reads in the core Evidence Gate flow must
   hit a real local DataHub instance loaded with `showcase-ecommerce`. Mocks
   are only acceptable in unit tests, clearly isolated from the demo path.
2. **Approve/block decisions are deterministic.** The rules engine decides.
   The LLM's job is limited to: explaining the evidence in plain language,
   drafting the remediation patch/test, and summarizing precedent
   differences. The LLM must never be the thing that flips a decision from
   `blocked` to `approved`.
3. **Validation is read-only and allow-listed.** The Analytics Agent / query
   layer may only run the specific, pre-registered comparison query for this
   MVP (old vs. proposed revenue aggregate over fixture data). No arbitrary
   query generation against production-shaped data.
4. **No autonomous merges or production writes.** The system's only write
   target is the Decision Provenance artifact on DataHub metadata. It never
   merges a PR, deploys a change, or writes to the underlying warehouse.
5. **One change type for the MVP.** `order_total` → `recognized_revenue` in
   the `order_entry_db.analytics.order_details` Snowflake dataset (verified
   real field in showcase-ecommerce, linked to the "Order Total" and
   "Revenue by Customer Class" glossary terms — see docs/setup.md for the
   Milestone 1 discovery). Do not generalize the schema-diff parser to
   arbitrary change types until this one path is fully verified.
6. **Scope is closed unless this file is edited first.** Do not add
   multi-agent handoff, policy-as-code gates, ML promotion mode, or the
   counterfactual simulator. If you believe one is necessary, stop and flag
   it — don't silently expand scope mid-build.

## Build order (do not reorder)

Each milestone has a **Definition of Done**. Do not move to the next
milestone until every item in the current one is checked, with the stated
evidence — not "should work."

### Milestone 1 — Foundation

**Environment: this project is built inside a GitHub Codespace, not on a
local machine.** The dev laptop has limited RAM/storage; DataHub Quickstart
needs Docker + 8GB RAM, which the codespace provides. Do not attempt to run
DataHub locally on the host machine — always assume the terminal you're in
is the codespace terminal.

Build:
- `.devcontainer/devcontainer.json` enabling the `docker-in-docker` feature
  plus a Python base image, so any fresh codespace gets Docker and Python
  ready with no manual setup.
- DataHub Quickstart running inside the codespace (`datahub docker
  quickstart`) with `showcase-ecommerce` loaded.
- A minimal MCP client call that retrieves the `order_total`-bearing dataset
  and its field-level lineage.
- `ChangeRequest` and `DecisionReceipt` JSON schemas (see Data Contracts
  below) as typed models (Pydantic or equivalent).

Definition of Done (verify, don't assume):
- [ ] The codespace was actually created and rebuilt from
      `.devcontainer/devcontainer.json` (not a manually patched host) —
      confirm `docker --version` works with no manual install step.
- [ ] `curl`/script output shows a real DataHub asset URN, not a placeholder.
- [ ] The lineage response includes at least one real downstream asset from
      `showcase-ecommerce` (screenshot or logged JSON, not asserted from
      memory).
- [ ] `ChangeRequest`/`DecisionReceipt` schemas validate against the example
      payloads in `examples/`.
- [ ] Port 9002 (DataHub UI) is reachable via the codespace's forwarded-port
      URL, and this URL is noted in `docs/setup.md` for the next session.

### Milestone 2 — Decision path

Build:
- Schema-diff parser for the one supported change type.
- Evidence bundle construction via Agent Context Kit (bounded, task-specific
  — not a full metadata dump).
- Deterministic risk rules (see Decision Rules Table below) producing a
  risk score and a preliminary `needs-review` / `approved` / `blocked`
  leaning, before validation runs.

Definition of Done:
- [ ] Feeding `fixtures/net_revenue_rename.json` produces a populated
      evidence bundle containing real owners, the `Revenue` glossary term,
      and downstream dashboard names pulled from DataHub — not stubbed.
- [ ] Risk rules are covered by unit tests for each row in the Decision
      Rules Table (see below), including the "no downstream consumers"
      risk-reducing case.
- [ ] Changing a rule input (e.g., removing the glossary link) visibly
      changes the computed risk score in a test.

### Milestone 3 — Validation and remediation

Build:
- Revenue compatibility query (DuckDB or fixture DB) comparing old vs.
  proposed aggregates.
- dbt-compatible compatibility view/patch generator.
- Migration test file generator.
- Final approve/block/needs-review outcome combining rules + validation.

Definition of Done:
- [ ] Running the fixture produces a `blocked` result with a stated numeric
      delta (e.g., "changes revenue by 13.16%") — the number must come
      from the actual query, not be hardcoded in a template string.
- [ ] The generated patch file is syntactically valid dbt/SQL and is saved
      into `examples/`.
- [ ] Unit test asserts: given the fixture's known delta, the outcome is
      deterministically `blocked` on two separate runs (no LLM-introduced
      variance in the pass/fail line).

### Milestone 4 — Write-back, invalidation, precedent, demo

Build:
- Decision Provenance write-back (structured properties, links, docs,
  tags, and an assertion/incident where appropriate) to the affected
  DataHub asset(s).
- A second, separate process/session that retrieves that provenance and
  answers "why was this blocked?" using only the written-back data.
- A graph-change watcher: simulate one change to an evidence input
  (policy, schema, lineage edge, owner, or quality state) and mark the
  related provenance `stale`, requiring revalidation.
- Precedent retrieval: submit a second, similar change request and show it
  retrieving the first provenance, reusing what still applies, and
  explicitly naming what has changed.
- Clean CLI/UI output or timeline suitable for the demo video.

Definition of Done:
- [ ] Opening the DataHub UI for the affected asset shows the Decision
      Provenance fields (rationale, evidence, validation, risk, approvers,
      revalidate_after) attached and human-readable — screenshot this.
- [ ] A fresh, independent script invocation (new process, not reused
      in-memory state) retrieves and correctly reports the prior decision.
- [ ] After the simulated graph change, the same asset's provenance status
      reads `stale` in DataHub, not just in application logs.
- [ ] The second, similar change request's output explicitly lists which
      prior evidence is reused and which conditions differ — not a generic
      "similar case found" message.
- [ ] Full demo script (see plan doc) runs start-to-finish from a fresh
      `git clone` using only the documented setup commands.

### Milestone 5 — Tests, docs, OSS contribution, submission polish

- [ ] Unit tests exist and pass for: risk scoring, validation failure,
      write-back payload creation, invalidation trigger, precedent
      comparison. Run the full suite and paste the passing output into
      `docs/test-report.md`.
- [ ] `examples/` contains: the schema diff, evidence bundle, blocked
      decision, generated patch, and written-back provenance payload —
      real captured output, not authored by hand.
- [ ] README quickstart works from a genuinely fresh clone (test in a clean
      directory or container, not your dev environment with cached state).
- [ ] The four DataHub Skills in `skills/` are each independently
      documented and runnable outside the main app.
- [ ] Open (or confirm) the upstream DataHub PR/issue; link it in
      `docs/oss-contribution.md` and the Devpost submission.
- [ ] Record the demo video (2:30–2:50) following the demo script in the
      plan doc; confirm it is under the 3:00 hard limit before uploading.

## Data contracts

### ChangeRequest (input)

```json
{
  "change_id": "string",
  "change_type": "field_rename",
  "source_asset": "urn:li:dataset:(...)",
  "old_field": "order_total",
  "new_field": "recognized_revenue",
  "old_type": "decimal",
  "new_type": "decimal",
  "pr_url": "https://github.com/example/repo/pull/42"
}
```

### Decision Provenance (write-back)

Use the exact shape already specified in the project plan doc — do not
invent new top-level fields without updating this file first:

```yaml
decision_id: eg-2026-001
status: needs-review | approved | blocked
change_url: <PR URL>
business_rationale: <one or two sentences>
affected_assets: [<urns>]
graph_snapshot_at: <ISO timestamp>
risk_score: <0-100>
evidence_checked: [<list>]
validation:
  result: passed | failed
  reason: <specific, numeric where possible>
required_approvers: [<role/owner>]
recommended_action: <string>
revalidate_after: <ISO date>
invalidation_inputs: [<list of graph dependencies that, if changed, void this>]
```

## Decision rules table (implement exactly, then extend only via tests)

| Signal | Effect |
|---|---|
| Field is in an executive dashboard lineage path | Increase risk |
| Field is linked to a glossary term such as Revenue | Increase risk |
| New field has incompatible type or semantic definition | Block |
| Validation aggregate differs outside tolerance | Block |
| No downstream consumers | Reduce risk |
| Existing quality assertion is failing | Block |
| Required approvals and all deterministic checks pass | Approve with migration plan |

**Decided simplification (do not re-litigate this mid-build):** the
showcase-ecommerce sample data has no "executive dashboard" label or tag on
any BI asset. For this MVP, treat **"has any downstream BI/dashboard
consumer at all"** as satisfying the "executive dashboard lineage path"
risk-increasing rule — do not invent or assign an "executive" label to a
sample asset that doesn't carry one in DataHub. The inverse rule ("no
downstream consumers → reduce risk") already gives you the signal in the
other direction, so this simplification doesn't lose test coverage. If this
ever needs to be more precise (e.g. distinguishing an executive dashboard
from an ordinary one), that requires a real signal in DataHub — a tag,
title convention, or owner role — not a hardcoded guess.

## Verification discipline

For every milestone, "verified" means one of:
- A command was actually run and its real output is pasted into the PR/commit
  message or `docs/test-report.md`, or
- A screenshot of the actual DataHub UI state is captured, or
- A test exists, actually executes, and its pass/fail is shown — not
  described.

"Should work," "this follows the pattern from the plan," or "I implemented
it the same way as X" are not verification. If something cannot be verified
yet (e.g., blocked on an external dependency), say so explicitly rather than
marking the checklist item done.

## Failure handling the demo must show gracefully

Do not let these crash the flow — handle and surface them cleanly, since the
Technical Execution criterion explicitly checks for this:
- Missing owner on an affected asset.
- Missing or broken lineage edge.
- Validation data source unavailable.
- Ambiguous semantic mapping between old and new field.

## When you are unsure

If a requirement here conflicts with what seems easiest to build, stop and
flag it rather than quietly resolving it in code. Scope changes and rule
changes both require updating this file first, so the build guide and the
implementation never drift apart.
