"""
scripts/ingest_and_categorize.py
End-to-end: choose CSV -> parse -> dicts_to_transactions -> auto_categorize -> print

Usage:
  python scripts/ingest_and_categorize.py

  Author - Luke Graham
  Date - 10/6/25
"""

from datetime import datetime               # used to timestamp uploads
from pathlib import Path                    # for building file paths

from core.categorize_edit import (          # import main categorization pipeline
    CategoryRules,                          # rule loader and matcher
    dicts_to_transactions,                  # convert list[dict] -> list[Transaction]
    auto_categorize,                        # categorize transactions
)
from core.models import Transaction         # unified Transaction model
from fileUpload.fileUpload import get_filename, upload_statement  # file selection + CSV reader

# resolve project root two levels up (../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # locate project root
RULES_PATH = PROJECT_ROOT / "data" / "rules.json"      # point to rules.json in /data


def print_table(title: str, rows: list[Transaction]) -> None:            # pretty-print results table
    print("\n" + title)                                                  # section title
    print("-" * len(title))                                              # underline with dashes
    print(f"{'ID':<10} {'Date':<10} {'Description':<40} {'Amount':>10}  {'Category':<16} {'Notes'}")  # table header
    print("-" * 110)                                                     # divider
    for t in rows:                                                       # iterate each transaction
        desc = (t.description[:37] + "...") if len(t.description) > 40 else t.description  # clip long descriptions
        print(f"{t.id:<10} {t.date.strftime('%Y-%m-%d'):<10} {desc:<40} {str(t.amount):>10}  {t.category:<16} {t.notes}")  # formatted row
    print("-" * 110)                                                     # footer divider


def main() -> None:                                      # main program entry
    # 1) pick a file and read CSV -> list[dict]
    csv_path = get_filename()                             # open file picker dialog
    rows = upload_statement(csv_path) or []               # read CSV rows into list of dicts

    # 2) convert dicts -> Transaction (keeps raw row; normalizes description)
    txns = dicts_to_transactions(                         # transform to Transaction model
        rows,
        source_name="wells-fargo",                        # mark data source
        source_upload_id=f"upload-{datetime.now().isoformat(timespec='seconds')}",  # unique upload ID
    )

    # 3) load rules and categorize
    rules = CategoryRules.from_json(RULES_PATH)           # load category rules from JSON file
    auto_categorize(txns, rules, overwrite=False)         # apply auto-categorization (skip manual overrides)

    # 4) show a quick summary
    print_table("Categorized Transactions", txns)         # print summary table of results


if __name__ == "__main__":  # only run if executed directly
    main()                  # call main function
