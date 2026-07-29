# Skill: Find Similar Precedents

Queries DataHub live metadata graph for prior Decision Provenance artifacts and produces an explicit comparison detailing what still applies, what differs, and what evidence can be reused.

## Inputs
- `--urn` (string): Candidate dataset URN.
- `--old-field` (string): Existing field name.
- `--new-field` (string): Proposed field name.
- `--change-id` (string): Candidate change request ID.
- `--pr-url` (string): Candidate pull request URL.
- `--json` (flag): Output raw precedent search JSON.

## Outputs
- List of matching prior decision IDs, prior status/risk, explicit `what_still_applies` items, explicit `what_differs` items, and reused evidence list.

## Example Invocation
```bash
python -m skills.find_similar_precedents --urn "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details_replica,PROD)" --old-field order_total --new-field recognized_revenue
```
