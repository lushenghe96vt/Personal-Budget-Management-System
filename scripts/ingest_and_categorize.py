"""
scripts/ingest_and_categorize.py
End-to-end: choose CSV -> detect bank -> parse -> dicts_to_transactions -> auto_categorize -> print

Usage:
  python scripts/ingest_and_categorize.py

  Author - Luke Graham
  Date - 10/13/25
"""

from datetime import datetime               # used for timestamps
from pathlib import Path                    # path manipulation for locating files

from core.categorize_edit import (          # import categorization pipeline
    CategoryRules,                          # rules loader / matcher
    dicts_to_transactions,                  # convert list[dict] -> list[Transaction]
    auto_categorize,                        # categorize transactions
)
from core.models import Transaction         # unified Transaction model
from fileUpload.fileUpload import (         # import file selection + parser + enum
    get_filename,
    upload_statement,
    Banks,
)

# resolve project root two levels up (../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # locate project root
RULES_PATH = PROJECT_ROOT / "data" / "rules.json"       # path to JSON rules file


def print_table(title: str, rows: list[Transaction]) -> None:
    """Pretty-print a formatted summary table of transactions."""
    print("\n" + title)
    print("-" * len(title))
    print(f"{'ID':<10} {'Date':<10} {'Description':<40} {'Amount':>10}  {'Category':<16} {'Notes'}")
    print("-" * 110)
    for t in rows:
        desc = (t.description[:37] + "...") if len(t.description) > 40 else t.description
        print(f"{t.id:<10} {t.date.strftime('%Y-%m-%d'):<10} {desc:<40} {str(t.amount):>10}  {t.category:<16} {t.notes}")
    print("-" * 110)


def main() -> None:
    """Main program entry point for ingestion + categorization demo."""

    # 1) Prompt for file path
    csv_path = get_filename()                                # open OS file picker dialog
    if not csv_path:
        print("No file selected.")
        return

    # 2) Determine likely bank type from filename (quick heuristic)
    lower_name = csv_path.lower()
    if "chase" in lower_name:
        bank_type = Banks.CHASE
    elif "wells" in lower_name or "wf" in lower_name:
        bank_type = Banks.WELLS_FARGO
    else:
        # default to Wells if unknown (since format is simple)
        bank_type = Banks.WELLS_FARGO

    print(f"Detected Bank: {bank_type.name.replace('_', ' ').title()}")

    # 3) Parse CSV → list[dict]
    rows = upload_statement(csv_path, bank=bank_type) or []
    if not rows:
        print("No rows found in file.")
        return

    # 4) Convert dicts → Transaction objects
    txns = dicts_to_transactions(
        rows,
        source_bank=bank_type,                              # pass in detected bank type
        source_name=bank_type.name.lower(),
        source_upload_id=f"upload-{datetime.now().isoformat(timespec='seconds')}",
    )

    # 5) Load categorization rules
    rules = CategoryRules.from_json(RULES_PATH)             # load category patterns from JSON

    # 6) Apply auto-categorization
    auto_categorize(txns, rules, overwrite=False)

    # 7) Display result table
    print_table("Categorized Transactions", txns)


if __name__ == "__main__":
    main()
