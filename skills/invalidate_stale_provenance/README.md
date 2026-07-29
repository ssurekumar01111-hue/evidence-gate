# Skill: Invalidate Stale Provenance

Inspects live DataHub graph dependencies for a target asset. If any graph input (such as a glossary term link) has changed since the Decision Provenance was issued, updates `eg_provenance_status` to `stale` on DataHub GMS.

## Inputs
- `--urn` (string): Target dataset URN on DataHub.
- `--simulate-remove-glossary` (flag): Simulates a graph mutation (removing Revenue glossary term link) prior to checking staleness.
- `--restore-terms` (flag): Restores original dataset glossary terms on DataHub.
- `--json` (flag): Output raw JSON result.

## Outputs
- Updated provenance status (`stale` or `active`), staleness reason, and boolean confirmation of GMS write-back.

## Example Invocation
```bash
python -m skills.invalidate_stale_provenance --urn "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)" --simulate-remove-glossary
```
And to restore original terms:
```bash
python -m skills.invalidate_stale_provenance --urn "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)" --restore-terms
```
