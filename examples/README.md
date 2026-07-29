# Examples Directory Index

This directory contains real, captured runtime artifacts produced during Evidence Gate execution against live DataHub GMS and metric validation datasets:

- **`change_request.json`**: Input `ChangeRequest` schema diff payload proposing `order_total` -> `recognized_revenue` on Snowflake `order_details`.
- **`evidence_bundle.json`**: Populated `EvidenceBundle` containing real owners (`David Kim`, `Julia Novak`), glossary terms (`Revenue by Customer Class`, `Order Total`), 13 downstream lineage consumers, and quality assertion metadata collected from DataHub.
- **`blocked_decision_receipt.json`**: Final deterministic `DecisionReceipt` payload combining Milestone 2 risk rules (Risk Score 75) and Milestone 3 DuckDB metric validation (13.16% shift -> BLOCKED).
- **`recognized_revenue_patch.sql`**: Generated dbt/SQL compatibility model patch for `recognized_revenue`.
- **`test_recognized_revenue_migration.py`**: Generated pytest migration test file validating bounds and zero-discrepancy conditions.
- **`written_back_provenance.json`**: Real written-back metadata retrieved from DataHub GMS, including 13 dataset custom properties, PR documentation link, and operational incident status.
