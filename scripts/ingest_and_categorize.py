"""
scripts/ingest_and_categorize.py
End-to-end: choose CSV -> parse -> dicts_to_transactions -> auto_categorize -> print

Usage:
  python scripts/ingest_and_categorize.py

  Author - Luke Graham
  Date - 10/6/25
"""

from datetime import datetime
from pathlib import Path

from core.categorize_edit import (
    CategoryRules,
    dicts_to_transactions,
    auto_categorize,
    get_subscription_transactions,
    check_subscription_alerts,
)
from core.models import Transaction
from core.fileUpload import get_filename, upload_statement


# resolve project root two levels up (../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = PROJECT_ROOT / "data" / "rules.json"


def print_table(title: str, rows: list[Transaction]) -> None:
    """Pretty-print all categorized transactions."""
    print("\n" + title)
    print("-" * len(title))
    print(f"{'ID':<10} {'Date':<10} {'Description':<40} {'Amount':>10}  {'Category':<16} {'Notes'}")
    print("-" * 110)
    for t in rows:
        desc = (t.description[:37] + "...") if len(t.description) > 40 else t.description
        print(
            f"{t.id:<10} {t.date.strftime('%Y-%m-%d'):<10} "
            f"{desc:<40} {str(t.amount):>10}  {t.category:<16} {t.notes}"
        )
    print("-" * 110)


def print_subscription_summary(subs: list[Transaction]) -> None:
    """Print summary of detected subscriptions and their upcoming renewals."""
    if not subs:
        print("\nNo subscriptions detected.")
        return

    print("\nUpcoming Subscription Renewals")
    print("-------------------------------------------")
    print(f"{'Description':<40} {'Next Due':<15} {'Amount':>10} {'Status':>8}")
    print("-------------------------------------------")
    for s in subs:
        next_due = s.next_due_date.strftime("%Y-%m-%d") if s.next_due_date else "N/A"
        desc = (s.description_raw[:37] + "...") if len(s.description_raw) > 40 else s.description_raw
        # check if same numeric day (✅ exact match, ⚠️ clamped)
        same_day = (
            s.date.day == s.next_due_date.day if getattr(s, "next_due_date", None) else False
        )
        status = "✅" if same_day else "⚠️"
        print(f"{desc:<40} {next_due:<15} {str(s.amount):>10} {status:>8}")
    print("-------------------------------------------")


def main() -> None:
    """Main entry point."""
    # 1) select and load statement
    csv_path = get_filename()
    rows = upload_statement(csv_path) or []

    # 2) convert -> Transaction models
    txns = dicts_to_transactions(
        rows,
        source_name="wells-fargo",
        source_upload_id=f"upload-{datetime.now().isoformat(timespec='seconds')}",
    )

    # 3) auto-categorize
    rules = CategoryRules.from_json(RULES_PATH)
    auto_categorize(txns, rules, overwrite=False)

    # 4) show categorized results
    print_table("Categorized Transactions", txns)

    # 5) show subscription renewals
    subs = get_subscription_transactions(txns)
    alerts = check_subscription_alerts(subs, days_before=10)
    print_subscription_summary(subs)

    # 6) highlight upcoming alerts
    if alerts:
        print("\n⚠️  Upcoming Renewals Within 10 Days ⚠️")
        print("-------------------------------------------")
        for a in alerts:
            print(f"{a.description_raw} → {a.next_due_date.strftime('%Y-%m-%d')}")
        print("-------------------------------------------")


if __name__ == "__main__":
    main()
