# Open-Source Contribution

**Status: PR open**, pending review.

Pulled the write-back/precedent/staleness pattern out of Evidence Gate
into a standalone, generalized skill and submitted it upstream to
`datahub-project/datahub-skills`.

PR: https://github.com/datahub-project/datahub-skills/pull/71
Skill: `skills/datahub-decision-provenance/SKILL.md`

The skill is deliberately generalized beyond this project's specific
revenue-rename scenario — the risk rules and write-back mechanism apply
to any metadata change worth pausing on before it ships.
