# Skill: Assess Change Risk

Evaluates deterministic risk scoring rules and DuckDB metric validation for a proposed schema change request on DataHub metadata.

## Inputs
- `--urn` (string): Target dataset URN on DataHub.
- `--old-field` (string): Existing column name.
- `--new-field` (string): Proposed column name.
- `--fixture` (filepath, optional): Path to a ChangeRequest JSON payload fixture.
- `--json` (flag): Output raw `DecisionReceipt` JSON payload.

## Outputs
- Risk score (0-100), leaning (`approved`, `needs-review`, `blocked`), triggered signals, required approvers list, and DuckDB validation aggregate comparison.

## Example Invocation
```bash
python -m skills.assess_change_risk --fixture fixtures/net_revenue_rename.json
```
or
```bash
python -m skills.assess_change_risk --urn "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)" --old-field order_total --new-field recognized_revenue
```
