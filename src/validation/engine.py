from pathlib import Path
from typing import Union
import duckdb
from src.validation.schemas import RevenueValidationReport


# Allow-listed comparison query per Evidence Gate constraint #3
ALLOWLISTED_REVENUE_COMPATIBILITY_QUERY = """
SELECT 
    ROUND(SUM(order_total), 2) AS old_aggregate,
    ROUND(SUM(CASE 
        WHEN order_status NOT IN ('refunded', 'cancelled') 
        THEN (order_total - tax_amount) 
        ELSE 0 
    END), 2) AS proposed_aggregate
FROM orders;
"""


def validate_revenue_compatibility(
    csv_path: Union[str, Path] = "fixtures/order_book_fixture.csv",
    tolerance_pct: float = 1.0,
) -> RevenueValidationReport:
    """
    Executes the allow-listed DuckDB compatibility query against the order book fixture dataset.
    Computes old aggregate SUM(order_total) vs proposed recognized_revenue aggregate,
    and returns a RevenueValidationReport indicating pass or fail based on tolerance.
    """
    path = Path(csv_path)
    try:
        if not path.exists():
            return RevenueValidationReport(
                result="unavailable",
                reason=f"Validation source unavailable: Fixture CSV not found at {path}",
                old_aggregate=0.0,
                proposed_aggregate=0.0,
                delta_pct=0.0,
                tolerance_pct=tolerance_pct,
            )

        conn = duckdb.connect(database=":memory:")
        # Load synthetic order book CSV into DuckDB memory table
        conn.execute(f"CREATE TABLE orders AS SELECT * FROM read_csv_auto('{path}')")

        row = conn.execute(ALLOWLISTED_REVENUE_COMPATIBILITY_QUERY).fetchone()
        if not row or row[0] is None:
            return RevenueValidationReport(
                result="unavailable",
                reason="Validation source unavailable: Failed to compute revenue aggregates from DuckDB query",
                old_aggregate=0.0,
                proposed_aggregate=0.0,
                delta_pct=0.0,
                tolerance_pct=tolerance_pct,
            )
    except Exception as e:
        return RevenueValidationReport(
            result="unavailable",
            reason=f"Validation source unavailable: {e}",
            old_aggregate=0.0,
            proposed_aggregate=0.0,
            delta_pct=0.0,
            tolerance_pct=tolerance_pct,
        )

    old_aggregate = float(row[0])
    proposed_aggregate = float(row[1])

    if old_aggregate == 0.0:
        delta_pct = 0.0
    else:
        delta_pct = (abs(old_aggregate - proposed_aggregate) / old_aggregate) * 100.0

    delta_pct = round(delta_pct, 4)
    passed = delta_pct <= tolerance_pct

    if passed:
        result = "passed"
        reason = (
            f"Validation passed: Revenue aggregate shifted by {delta_pct:.2f}% "
            f"(within allowed tolerance of {tolerance_pct:.2f}%)."
        )
    else:
        result = "failed"
        reason = (
            f"Validation failed: Revenue aggregate shifted by {delta_pct:.2f}% "
            f"(exceeds allowed tolerance of {tolerance_pct:.2f}%). "
            f"Old SUM(order_total) = ${old_aggregate:,.2f}, Proposed Recognized Revenue = ${proposed_aggregate:,.2f}."
        )

    return RevenueValidationReport(
        result=result,
        reason=reason,
        old_aggregate=old_aggregate,
        proposed_aggregate=proposed_aggregate,
        delta_pct=delta_pct,
        tolerance_pct=tolerance_pct,
    )
