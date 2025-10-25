"""
core/categorize_edit.py

Team 8 — Personal Budget Management System
  Author - Luke Graham
  Date - 10/6/25
"""

from __future__ import annotations
import json, re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from calendar import monthrange
from core.models import Transaction


# -------------------- rules engine --------------------

class CategoryRules:
    def __init__(self, compiled: List[Tuple[str, List[re.Pattern]]]):
        self._compiled = compiled

    @classmethod
    def from_json(cls, path: Path) -> "CategoryRules":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("rules.json must be an object of {category: [patterns...]}")
        compiled: List[Tuple[str, List[re.Pattern]]] = []
        for category, patterns in data.items():
            if not isinstance(patterns, Sequence):
                raise ValueError(f"Category '{category}' must map to a list of patterns.")
            pats: List[re.Pattern] = []
            for p in patterns:
                if not isinstance(p, str):
                    raise ValueError(f"Pattern in '{category}' must be a string.")
                pats.append(
                    re.compile(p[3:], re.I) if p.startswith("re:") else re.compile(re.escape(p), re.I)
                )
            compiled.append((category, pats))
        return cls(compiled)

    def suggest(self, description: str) -> Optional[str]:
        text = _prep_desc_for_rules(description)
        for cat, pats in self._compiled:
            if any(p.search(text) for p in pats):
                return cat
        return None


# -------------------- categorization --------------------

def auto_categorize(transactions: Iterable[Transaction], rules: CategoryRules, *, overwrite=False) -> None:
    for t in transactions:
        if not overwrite and (t.user_override or (t.category and t.category != "Uncategorized")):
            continue

        cat = rules.suggest(t.description or "")
        if cat:
            t.category = cat

        desc_low = t.description_raw.lower()

        # 🔹 Detect "recurring payment authorized on XX/XX" patterns
        if "recurring payment" in desc_low or t.category.lower() == "subscriptions":
            t.is_subscription = True

            # Match date after "authorized on" (like "RECURRING PAYMENT AUTHORIZED ON 10/02" or "10/02/25")
            m = re.search(
                r"(?:recurring payment\s+authorized\s+on\s+)(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
                t.description_raw,
                re.IGNORECASE,
            )
            if m:
                parsed = _parse_date(m.group(1))
                if parsed:
                    t.date = parsed

    detect_recurring_subscriptions(transactions)
    estimate_next_due_dates(transactions)


def set_category(txn: Transaction, category: str, *, mark_override=True):
    txn.category = (category or "").strip() or "Uncategorized"
    if mark_override:
        txn.user_override = True


def set_notes(txn: Transaction, notes: str):
    txn.notes = (notes or "").strip()[:2048]


# -------------------- subscription logic --------------------

def detect_recurring_subscriptions(transactions: List[Transaction]) -> None:
    grouped: Dict[str, List[Transaction]] = {}
    for t in transactions:
        key = t.description_raw.lower().strip()
        grouped.setdefault(key, []).append(t)

    for key, txns in grouped.items():
        if len(txns) < 2:
            continue
        txns.sort(key=lambda x: x.date)
        diffs = [(txns[i].date - txns[i - 1].date).days for i in range(1, len(txns))]
        avg = sum(diffs) / len(diffs)
        if 25 <= avg <= 33:
            for t in txns:
                t.is_subscription = True


def estimate_next_due_dates(transactions: List[Transaction]) -> None:
    """Estimate next due dates — always the same numeric day next month."""
    grouped: Dict[str, List[Transaction]] = {}
    for t in transactions:
        if not getattr(t, "is_subscription", False):
            continue
        key = t.description_raw.lower().strip()
        grouped.setdefault(key, []).append(t)

    for desc, txns in grouped.items():
        txns.sort(key=lambda x: x.date)
        for t in txns:
            t.next_due_date = _same_day_next_month(t.date)


def _same_day_next_month(date: datetime) -> datetime:
    """Return same day next month (2 → 2, 31 → last valid day of next month)."""
    y, m = date.year, date.month
    if m == 12:
        y, m = y + 1, 1
    else:
        m += 1
    max_day = monthrange(y, m)[1]
    d = min(date.day, max_day)
    return date.replace(year=y, month=m, day=d)


def check_subscription_alerts(transactions: List[Transaction], days_before: int = 7) -> List[Transaction]:
    today = datetime.now()
    alerts = []
    for t in transactions:
        if not getattr(t, "is_subscription", False) or not getattr(t, "next_due_date", None):
            continue
        days_left = (t.next_due_date - today).days
        if 0 < days_left <= days_before and not getattr(t, "alert_sent", False):
            alerts.append(t)
            t.alert_sent = True
    return alerts


def get_subscription_transactions(transactions: List[Transaction]) -> List[Transaction]:
    return [t for t in transactions if getattr(t, "is_subscription", False)]


# -------------------- transaction building --------------------

_DEFAULT_MAP = {
    "id": ["Id", "ID", "TransactionId", "Ref", "Reference"],
    "date": ["Date", "Transaction Date", "Posted Date", "Posting Date"],
    "posted_date": ["Posted Date", "Posting Date"],
    "description": ["Description", "Memo", "Details", "Name"],
    "amount": ["Amount", "Transaction Amount", "Value"],
    "debit": ["Debit", "Withdrawal", "Outflow"],
    "credit": ["Credit", "Deposit", "Inflow"],
    "balance": ["Balance", "Running Balance"],
    "type": ["Type", "Transaction Type", "Category"],
    "currency": ["Currency", "CCY"],
}

_DATE_FORMATS = [
    "%Y-%m-%d",     # ISO (2025-09-02)
    "%m/%d/%Y",     # U.S.
    "%m/%d/%y",     # U.S. short
    "%b %d %Y",     # Sep 02 2025
    "%d %b %Y",     # 02 Sep 2025 (fallback)
]


def dicts_to_transactions(rows: Iterable[dict], *, source_name="unknown", source_upload_id="", field_map=None, default_currency="USD") -> List[Transaction]:
    fmap = {**_DEFAULT_MAP, **(field_map or {})}
    out: List[Transaction] = []
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue
        rid = _pick_first(r, fmap["id"]) or f"row:{i}"
        amt = _parse_amount(r, fmap)
        raw_desc = _pick_first(r, fmap["description"]) or ""
        norm_desc = _normalize_for_match(_strip_boilerplate(raw_desc))
        date_str = _pick_first(r, fmap["date"]) or ""
        date = _parse_date(date_str) or datetime.now()
        posted_str = _pick_first(r, fmap["posted_date"]) or ""
        posted = _parse_date(posted_str) if posted_str else None
        bal = _parse_decimal(_pick_first(r, fmap["balance"]))
        txn_type = (_pick_first(r, fmap["type"]) or "").strip()
        currency = (_pick_first(r, fmap["currency"]) or default_currency).strip().upper()

        txn = Transaction(
            id=str(rid),
            date=date,
            posted_date=posted,
            description=norm_desc or (raw_desc.strip()),
            description_raw=raw_desc.strip(),
            amount=amt,
            balance=bal,
            txn_type=txn_type,
            currency=currency or default_currency,
            category="Uncategorized",
            notes="",
            user_override=False,
            source_name=source_name,
            source_upload_id=source_upload_id,
            raw=dict(r),
        )
        out.append(txn)
    return out


def _pick_first(row: dict, cands: List[str]) -> Optional[str]:
    for c in cands:
        if c in row and str(row[c]).strip():
            return str(row[c]).strip()
    return None


def _parse_amount(row: dict, fmap: Dict[str, List[str]]) -> Decimal:
    val = _pick_first(row, fmap["amount"])
    if val is not None:
        d = _parse_decimal(val)
        if d is not None:
            return d
    debit = _pick_first(row, fmap["debit"])
    credit = _pick_first(row, fmap["credit"])
    if debit:
        return -abs(_parse_decimal(debit) or Decimal("0"))
    if credit:
        return abs(_parse_decimal(credit) or Decimal("0"))
    return Decimal("0")


def _parse_decimal(v: Optional[str]) -> Optional[Decimal]:
    if not v:
        return None
    s = v.replace(",", "").replace("$", "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _parse_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for f in _DATE_FORMATS:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# -------------------- description cleaning --------------------

_BOILER_FRAGMENTS = [
    "purchase authorized", "purchase auth", "pos purchase",
    "debit card purchase", "debit purchase", "card purchase",
    "signature purchase", "contactless",
    "recurring payment authorized", "recurring payment",
    "authorization", "authorized",
    "atm withdrawal", "non-wf atm", "withdrawal authorized",
    "online transfer", "internal transfer",
    "posted on", "post date",
]
_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.I)
_CARD_RE = re.compile(r"\b(?:card|debit)\s*\d{2,6}\b", re.I)
_NUMBLOB_RE = re.compile(r"\b\d{6,}\b")
_SUFFIX_RE = re.compile(r"\b(llc|inc|co|corp|ltd|llp|plc)\b", re.I)
_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^a-z0-9\s&'-]+")


def _strip_boilerplate(d: str) -> str:
    s = d.lower()
    for frag in _BOILER_FRAGMENTS:
        s = s.replace(frag, " ")
    s = _DATE_RE.sub(" ", s)
    s = _CARD_RE.sub(" ", s)
    s = _NUMBLOB_RE.sub(" ", s)
    return s


def _normalize_for_match(s: str) -> str:
    s = s.lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _SUFFIX_RE.sub(" ", s)
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def _prep_desc_for_rules(d: str) -> str:
    return _normalize_for_match(_strip_boilerplate(d or ""))


# -------------------- CLI --------------------

def _cli(argv: List[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Suggest a category for a description using rules.json")
    p.add_argument("rules", type=Path)
    p.add_argument("--desc", required=True)
    args = p.parse_args(argv)
    rules = CategoryRules.from_json(args.rules)
    cat = rules.suggest(args.desc)
    print(cat or "Uncategorized")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_cli(sys.argv[1:]))
