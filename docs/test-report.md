# Evidence Gate — Automated Test Report

**Date:** 2026-07-29  
**Status:** **24 passed in 7.62s (100% Pass)**

## Test Execution Output

```text
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/python/3.11.15/bin/python3
cachedir: .pytest_cache
rootdir: /workspaces/evidence-gate
plugins: anyio-4.14.2
collected 24 items

examples/test_recognized_revenue_migration.py::test_recognized_revenue_calculation PASSED [  4%]
examples/test_recognized_revenue_migration.py::test_recognized_revenue_bounds_and_non_negative PASSED [  8%]
tests/test_milestone2.py::test_schema_diff_parser_field_rename PASSED    [ 12%]
tests/test_milestone2.py::test_evidence_bundle_construction_from_datahub PASSED [ 16%]
tests/test_milestone2.py::test_rule_revenue_glossary_term_linked PASSED  [ 20%]
tests/test_milestone2.py::test_rule_downstream_bi_consumer PASSED        [ 25%]
tests/test_milestone2.py::test_rule_no_downstream_consumers_reduces_risk PASSED [ 29%]
tests/test_milestone2.py::test_rule_incompatible_type_blocks PASSED      [ 33%]
tests/test_milestone2.py::test_rule_failing_quality_assertion_blocks PASSED [ 37%]
tests/test_milestone2.py::test_rule_input_change_visibly_changes_risk_score PASSED [ 41%]
tests/test_milestone2.py::test_end_to_end_milestone2_decision_path PASSED [ 45%]
tests/test_milestone3.py::test_duckdb_validation_query_and_delta PASSED  [ 50%]
tests/test_milestone3.py::test_deterministic_validation_runs_twice PASSED [ 54%]
tests/test_milestone3.py::test_validation_failure_overrides_low_risk_score PASSED [ 58%]
tests/test_milestone3.py::test_validation_success_retains_milestone2_risk_score PASSED [ 62%]
tests/test_milestone3.py::test_remediation_artifacts_generation PASSED   [ 66%]
tests/test_milestone3.py::test_generated_migration_test_executes PASSED  [ 70%]
tests/test_milestone4.py::test_writeback_decision_provenance_to_datahub PASSED [ 75%]
tests/test_milestone4.py::test_independent_retrieval_from_datahub PASSED [ 79%]
tests/test_milestone4.py::test_graph_change_watcher_staleness_flip_on_datahub PASSED [ 83%]
tests/test_milestone4.py::test_precedent_retrieval_and_comparison PASSED [ 87%]
tests/test_schemas.py::test_change_request_schema PASSED                 [ 91%]
tests/test_schemas.py::test_change_request_fixture PASSED                [ 95%]
tests/test_schemas.py::test_decision_receipt_schema PASSED               [100%]

============================== 24 passed in 7.62s ==============================
```

## Suite Summary
- **Milestone 1:** ChangeRequest & DecisionReceipt Schema Validations (3 tests)
- **Milestone 2:** Discovery, Evidence Bundle & Risk Engine (9 tests)
- **Milestone 3:** Metric Validation, dbt Patch & Migration Test Generator (6 tests)
- **Milestone 4:** DataHub Provenance Write-Back, Retrieval, Invalidation Watcher & Precedents (4 tests)
- **Examples Verification:** Migration SQL & Test Suite (2 tests)
