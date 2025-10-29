"""
scripts/quick_demo.py
Quick end-to-end of auto-categorization + manual edits against the Transaction model.

Usage:
  python scripts/quick_demo.py

  Author - Luke Graham
  Date - 10/6/25
"""

from datetime import datetime                  # for creating sample transaction dates
from decimal import Decimal                    # for accurate currency calculations

from core.models import Transaction            # import unified Transaction model
from core.categorize_edit import (             # import core categorization/edit functions
    CategoryRules,                             # rule engine for categorization
    auto_categorize,                           # main auto-categorization function
    set_category,                              # manually set a category
    set_notes,                                 # manually attach a note
)
from core.view_spending import (
    spending_summary,
    show_pie,
    show_table,
    income_summary
)


def make_sample_transactions() -> list[Transaction]:                     # create sample dataset
    # minimal fields for Transaction: id, date, description, amount
    return [
        Transaction(id="t1", date=datetime(2025, 9, 25), description="Kroger #123 Blacksburg VA", amount=Decimal("-54.12")),   # grocery
        Transaction(id="t2", date=datetime(2025, 9, 26), description="Starbucks Store 8876", amount=Decimal("-6.45")),          # dining
        Transaction(id="t3", date=datetime(2025, 9, 26), description="UBER TRIP HELP.UBER.COM", amount=Decimal("-18.20")),      # transit
        Transaction(id="t4", date=datetime(2025, 9, 27), description="SHELL OIL 12345679", amount=Decimal("-42.05")),           # gas
        Transaction(id="t5", date=datetime(2025, 9, 27), description="Stripe Payout 2025-09-25", amount=Decimal("350.00")),     # income
        Transaction(id="t6", date=datetime(2025, 9, 28), description="Apartment Leasing Office", amount=Decimal("-800.00")),    # rent
        Transaction(id="t7", date=datetime(2025, 9, 28), description="Spotify P07 Family Plan", amount=Decimal("-15.99")),      # entertainment
        Transaction(id="t8", date=datetime(2025, 9, 29), description="Food Lion 778", amount=Decimal("-73.88")),                # grocery
        Transaction(id="t9", date=datetime(2025, 9, 29), description="Random Merchant Not In Rules", amount=Decimal("-9.99")),  # uncategorized
    ]


def print_table(title: str, rows: list[Transaction]) -> None:                              # print formatted transaction table
    print("\n" + title)                                                                    # print section title
    print("-" * len(title))                                                                # underline title
    print(f"{'ID':<4} {'Date':<10} {'Description':<36} {'Amount':>9}  {'Category':<15} {'Notes'}")  # header row
    print("-" * 100)                                                                       # divider line
    for t in rows:                                                                         # loop through all transactions
        desc = (t.description[:33] + "...") if len(t.description) > 36 else t.description  # clip long descriptions
        print(f"{t.id:<4} {t.date.strftime('%Y-%m-%d'):<10} {desc:<36} {str(t.amount):>9}  {t.category:<15} {t.notes}")  # display row
    print("-" * 100)                                                                       # bottom divider


def main() -> None:                            # demo entry point
    txns = make_sample_transactions()          # generate example transactions

    # inline rules (same structure as rules.json)
    rule_dict = {                              # quick in-memory rule definitions
        "Groceries": ["kroger", "food lion", "aldi", "walmart"],           # grocery matches
        "Dining": ["starbucks", "chipotle", "mcdonald", "re:.*pizza.*"],   # dining & regex
        "Transit": ["uber", "lyft", "metro", "parking", "toll"],           # transit matches
        "Gas": ["shell", "exxon", "bp", "chevron", "speedway"],            # gas station keywords
        "Income": ["stripe payout", "payroll", "direct deposit", "venmo cashout"],  # income identifiers
        "Rent": ["leasing", "apartments", "property management", "rent"],  # rent-related
        "Entertainment": ["spotify", "netflix", "hulu", "steam", "apple tv"],  # entertainment matches
    }
    rules = CategoryRules.from_dict(rule_dict)  # build CategoryRules object from inline dict

    print_table("Before auto-categorize", txns)  # show initial transaction list

    auto_categorize(txns, rules, overwrite=False)  # apply rules to categorize transactions

    print_table("After auto-categorize", txns)  # show categorized output

    # manual tweak + note (simulate user correction)
    unknown = next(t for t in txns if t.id == "t9")              # find uncategorized transaction
    set_category(unknown, "Dining", mark_override=True)          # manually categorize as Dining
    set_notes(unknown, "Team lunch (manual)")                    # attach explanatory note

    print_table("After manual set_category + set_notes", txns)   # show final categorized table


    list_of_percents = spending_summary(txns)   # display spending summary via pie and table
    for row in list_of_percents:
        print(row)
    show_pie(list_of_percents)
    show_table(list_of_percents)

    spending_vs_income = income_summary(txns)

    for row in spending_vs_income:               # display spending vs. income
        print(row)
    show_pie(spending_vs_income)
    show_table(spending_vs_income)



if __name__ == "__main__":  # run demo when script is executed directly
    main()                  # call main function
