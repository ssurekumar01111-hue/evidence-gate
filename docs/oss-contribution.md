# Open-Source Contribution & DataHub Skills Integration

> [!IMPORTANT]
> **Pending User Decision:** No upstream pull request or issue has been opened yet against `datahub-project/datahub` or related repositories. Per build guidelines, external PR creation is flagged for user decision rather than fabricating a URL or submitting arbitrary external commits.

## Contributed DataHub Skills

Evidence Gate contributes four modular, published DataHub Skills under `skills/` designed to be registered or invoked independently by AI agents interacting with DataHub GMS:

1. **`skills/assess_change_risk`**: Evaluates deterministic risk scoring rules and metric validation for a proposed schema change request against live DataHub metadata.
2. **`skills/create_decision_provenance`**: Emits structured Decision Provenance metadata back to DataHub GMS (custom properties, documentation links, and operational incident assertions).
3. **`skills/find_similar_precedents`**: Queries DataHub live metadata graph for prior Decision Provenance artifacts and produces an explicit comparison detailing what still applies vs. what differs.
4. **`skills/invalidate_stale_provenance`**: Inspects live DataHub graph dependencies for a target asset and automatically updates provenance status to `stale` on DataHub GMS if dependencies changed.

## Next Steps for Upstream PR
When ready to submit upstream:
1. Target Repository: `datahub-project/datahub` (or `datahub-project/datahub-mcp`)
2. Proposed Contribution Scope: Registering Decision Provenance custom properties / aspect schema extensions and published agent skills.
