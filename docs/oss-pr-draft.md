# OSS Pull Request Draft: `datahub-project/datahub-skills`

> **Note:** This PR description uses the Conventional Commits title requirement (`feat: ...`) and incorporates the rationale written for `datahub-skills`.

---

## PR Title (Conventional Commits Format)
`feat: add datahub-decision-provenance skill`

---

## PR Description

# datahub-decision-provenance

## What this is

I built this while working on Evidence Gate for the DataHub Organizational Reasoning Hackathon (repo: https://github.com/ssurekumar01111-hue/evidence-gate).
The core idea: before a schema/metric change ships, an agent should be able to check DataHub's graph, run an actual validation query, and — if it matters enough to block — write the reasoning back onto the asset instead of losing it in a Slack thread or a PR comment nobody reads six months later.

That write-back part is the piece I think is generally useful outside my specific hackathon scenario, so I pulled it out into a standalone skill.

## What it does

Given a proposed change (field rename, type change, etc.), the skill:

1. Pulls the relevant context for the asset — lineage, glossary terms, owners, current quality assertions. Nothing exotic, just what's already in the graph.
2. Scores risk with a small set of rules (is it linked to a business glossary term, does it have downstream BI consumers, is there already a failing assertion on it).
3. Runs a validation check if one's configured, and combines that with the risk score into approve / block / needs-review.
4. If it's risky enough, writes the decision back onto the DataHub asset — custom properties, an institutional memory link to the PR, and a native incident if it's blocked. This is the part I actually care about: the *why* becomes part of the graph, not a separate audit log somewhere else.
5. Can also answer "why was this blocked?" later by reading that same write-back, and flags it stale if something it depended on (e.g. the glossary link) changes afterward.

None of this auto-merges anything or makes the approve/block call with an LLM — that part stays rule-based on purpose. The LLM's job here is explaining evidence and drafting migration patches, not deciding.

## Why I'm submitting it here instead of just leaving it in my repo

It's not tied to my hackathon's specific scenario (revenue field renames) — the risk rules and write-back mechanism generalize to any metadata change worth thinking twice about. Figured it's more useful sitting alongside `datahub-search` / `datahub-lineage` / `datahub-enrich` than buried in a one-off project repo.

Happy to adjust naming, trim the workflow steps, or split this differently if it overlaps with something already planned for this repo — just let me know.

---

## Submission Checklist (For Opening PR)

- [ ] **PR Title Format:** Set to `feat: add datahub-decision-provenance skill` per [CONTRIBUTING.md](file:///workspaces/evidence-gate/scratch/datahub-skills/CONTRIBUTING.md#L20-L34).
- [ ] **Pre-commit / Linting Hooks:** Run `pip install pre-commit && pre-commit run --all-files` locally to pass Prettier and markdownlint.
- [ ] **Branch Naming:** Create feature branch `feat/datahub-decision-provenance` on your fork of `datahub-project/datahub-skills`.
- [ ] **Target Branch:** Open PR against `datahub-project/datahub-skills:main`.
