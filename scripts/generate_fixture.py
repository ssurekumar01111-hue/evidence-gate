import random
import csv
from pathlib import Path


def generate_synthetic_order_fixture(file_path: Path = Path("fixtures/order_book_fixture.csv"), seed: int = 42) -> Path:
    """
    Generates a synthetic order book dataset for validation testing.
    SYNTHETIC FIXTURE COMMENT: Plausible order book representing 100 order-level transactions.
    This is synthetic test data used for metric comparison per SKILL.md constraint #3.
    """
    random.seed(seed)
    statuses = ["shipped", "delivered", "pending", "refunded", "cancelled"]
    # Weights: 50% delivered, 35% shipped, 5% pending, 5% refunded, 5% cancelled
    weights = [35, 50, 5, 5, 5]

    fieldnames = ["order_id", "order_total", "tax_amount", "discount_amount", "order_status"]
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(1, 101):
            order_id = 1000 + i
            gross_val = round(random.uniform(45.00, 350.00), 2)
            tax_rate = random.uniform(0.05, 0.08)
            tax_amount = round(gross_val * tax_rate, 2)
            discount_amount = round(random.uniform(0.00, 15.00), 2) if random.random() < 0.3 else 0.00
            order_status = random.choices(statuses, weights=weights)[0]
            
            writer.writerow({
                "order_id": order_id,
                "order_total": f"{gross_val:.2f}",
                "tax_amount": f"{tax_amount:.2f}",
                "discount_amount": f"{discount_amount:.2f}",
                "order_status": order_status,
            })
            
    return file_path


if __name__ == "__main__":
    path = generate_synthetic_order_fixture()
    print(f"Generated synthetic fixture at {path}")
