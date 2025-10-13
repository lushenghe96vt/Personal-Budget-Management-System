"""
scripts/ingest_and_categorize.py
End-to-end: choose CSV -> detect bank -> parse -> dicts_to_transactions -> auto_categorize -> manual edits -> print

Usage:
  python scripts/ingest_and_categorize.py

  Author - Luke Graham
  Date - 10/13/25
"""

from datetime import datetime                # used for timestamps
from pathlib import Path                     # for path handling

from core.categorize_edit import (           # import categorization pipeline
    CategoryRules,                           # rules loader / matcher
    dicts_to_transactions,                   # convert list[dict] -> list[Transaction]
    auto_categorize,                         # categorize transactions
    set_category,                            # manual category editing
    set_notes,                               # add/edit transaction notes
)
from core.models import Transaction          # unified Transaction model
from fileUpload.fileUpload import (          # file selection + parser + bank enum
    get_filename,
    upload_statement,
    Banks,
)


# -------------------- paths --------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent          # locate project root
RULES_PATH = PROJECT_ROOT / "data" / "rules.json"              # path to rules.json


# -------------------- helpers --------------------

def print_table(title: str, rows: list[Transaction]) -> None:
    """Pretty-print formatted transaction data."""
    print("\n" + title)
    print("-" * len(title))
    print(f"{'ID':<10} {'Date':<10} {'Description':<40} {'Amount':>10}  {'Category':<16} {'Notes'}")
    print("-" * 110)
    for t in rows:
        desc = (t.description[:37] + "...") if len(t.description) > 40 else t.description
        print(f"{t.id:<10} {t.date.strftime('%Y-%m-%d'):<10} {desc:<40} {str(t.amount):>10}  {t.category:<16} {t.notes}")
    print("-" * 110)


def find_transaction_by_id(rows: list[Transaction], row_id: str) -> Transaction | None:
    """Find a transaction by its row ID string (e.g., 'row:3')."""
    for t in rows:
        if t.id.strip().lower() == row_id.strip().lower():
            return t
    return None


def interactive_edit(txns: list[Transaction]) -> None:
    """Allow user to manually edit categories or notes after auto-categorization."""
    print("\nWould you like to edit any categories or add notes?")
    print("Type the row ID (e.g., row:3) to edit, or press Enter to finish.\n")

    while True:
        choice = input("Enter Row ID to edit (or Enter to finish): ").strip()
        if not choice:
            break  # done editing

        txn = find_transaction_by_id(txns, choice)
        if not txn:
            print("Invalid ID. Please try again.")
            continue

        print(f"\nEditing Transaction {txn.id}:")
        print(f"Description: {txn.description_raw}")
        print(f"Current Category: {txn.category}")
        print(f"Current Notes: {txn.notes}\n")

        new_cat = input("Enter new category (or press Enter to keep current): ").strip()
        if new_cat:
            set_category(txn, new_cat)
            print(f"Category updated to: {txn.category}")

        new_note = input("Enter a note (or press Enter to keep current): ").strip()
        if new_note:
            set_notes(txn, new_note)
            print(f"Note added: {txn.notes}")

        print("\nEdit complete. You can choose another transaction or press Enter to finish.\n")


# -------------------- main --------------------

def main() -> None:
    """Main program entry point."""
    # 1) Choose a CSV file
    csv_path = get_filename()
    if not csv_path:
        print("No file selected.")
        return

    # 2) Detect likely bank from filename
    lower_name = csv_path.lower()
    if "chase" in lower_name:
        bank_type = Banks.CHASE
    elif "wells" in lower_name or "wf" in lower_name:
        bank_type = Banks.WELLS_FARGO
    else:
        bank_type = Banks.WELLS_FARGO  # default fallback
    print(f"Detected Bank: {bank_type.name.replace('_', ' ').title()}")

    # 3) Load CSV → dicts
    rows = upload_statement(csv_path, bank=bank_type) or []
    if not rows:
        print("No rows found in file.")
        return

    # 4) Convert dicts → Transaction objects
    txns = dicts_to_transactions(
        rows,
        source_bank=bank_type,
        source_name=bank_type.name.lower(),
        source_upload_id=f"upload-{datetime.now().isoformat(timespec='seconds')}",
    )

    # 5) Load rules and apply auto-categorization
    rules = CategoryRules.from_json(RULES_PATH)
    auto_categorize(txns, rules, overwrite=False)

    # 6) Show categorized results
    print_table("Categorized Transactions", txns)

    # 7) Offer manual edits
    interactive_edit(txns)

    # 8) Display final results after edits
    print_table("Final Transactions (After Edits)", txns)


if __name__ == "__main__":
    main()
