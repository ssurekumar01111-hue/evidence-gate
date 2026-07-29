# Skill: Create Decision Provenance

Emits structured Decision Provenance metadata to DataHub GMS, including 13 dataset custom properties, PR documentation links, and operational incident assertions.

## Inputs
- `--fixture` (filepath): Path to ChangeRequest JSON payload fixture.
- `--json` (flag): Output raw write-back result JSON.

## Outputs
- Emitted aspect result detailing target asset URN, custom properties emitted count, documentation link URL, and native DataHub incident URN.

## Example Invocation
```bash
python -m skills.create_decision_provenance --fixture fixtures/net_revenue_rename.json
```
