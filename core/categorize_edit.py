from __future__ import annotations  # enable forward references in type hints (must be first)

"""
core/categorize_edit.py

Team 8 — Personal Budget Management System
  Author - Luke Graham
  Date - 10/6/25

Implements:
  - ID 7  : Auto-categorize transactions (ordered keyword/regex rules)
  - ID 13 : Manually edit a transaction's category
  - ID 14 : Add notes to a transaction

Notes
-----
* Rules are ordered: first matching category wins.
* Patterns: plain substrings (case-insensitive) or regex (prefix "re:").
* Descriptions are cleaned before matching to improve hit rate.
* Works automatically for both Wells Fargo and Chase exports.
"""

import json  # read/write JSON files for category rules
import re  # compile regexes for text pattern matching
from datetime import datetime  # handle transaction dates
from decimal import Decimal, InvalidOperation  # handle money safely (no float errors)
from pathlib import Path  # manage file paths
from typing import Dict, Iterable, List, Optional, Sequence, Tuple  # type hints

from core.models import Transaction  # import Transaction model class
from core.fileUpload import Banks  # import bank enum (CHASE, WELLS_FARGO)


# -------------------- rules engine --------------------

class CategoryRules:
    def __init__(self, compiled: List[Tuple[str, List[re.Pattern]]]):  # constructor
        self._compiled = compiled  # store [(category, [regex patterns])]

    @classmethod
    def from_json(cls, path: Path) -> "CategoryRules":  # load rules from JSON file
        data = json.loads(Path(path).read_text(encoding="utf-8"))  # read + parse JSON
        if not isinstance(data, dict):  # ensure top-level is a dict
            raise ValueError("rules.json must be an object of {category: [patterns...]}")  # enforce format
        compiled: List[Tuple[str, List[re.Pattern]]] = []  # prepare result list
        for category, patterns in data.items():  # iterate all rule categories
            if not isinstance(patterns, Sequence):  # must be a list
                raise ValueError(f"Category '{category}' must map to a list of patterns.")  # invalid format guard
            bucket: List[re.Pattern] = []  # holds compiled regex patterns
            for p in patterns:  # iterate raw string patterns
                if not isinstance(p, str):  # must be string
                    raise ValueError(f"Pattern in '{category}' must be a string.")  # error if not
                if p.startswith("re:"):  # regex pattern (explicit)
                    bucket.append(re.compile(p[3:], re.IGNORECASE))  # compile regex pattern
                else:  # plain substring match
                    bucket.append(re.compile(re.escape(p), re.IGNORECASE))  # escape + compile
            compiled.append((category, bucket))  # add (category, [compiled regexes])
        return cls(compiled)  # return CategoryRules instance

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "CategoryRules":  # alternative for dict input
        tmp = Path("__inline_rules__.json")  # temporary file
        tmp.write_text(json.dumps(data), encoding="utf-8")  # write dict to JSON
        try:
            return cls.from_json(tmp)  # parse via normal loader
        finally:
            try:
                tmp.unlink()  # clean up temp file
            except Exception:
                pass  # ignore errors

    def suggest(self, description: str) -> Optional[str]:  # return first matching category
        text = _prep_desc_for_rules(description)  # normalize text for comparison
        for category, patterns in self._compiled:  # iterate all categories
            for pat in patterns:  # iterate all patterns in category
                if pat.search(text):  # match found?
                    return category  # return category name
        return None  # no match


# -------------------- public API --------------------

def auto_categorize(
    transactions: Iterable[Transaction],  # list of transactions to categorize
    rules: CategoryRules,  # loaded rules
    *,
    overwrite: bool = False,  # overwrite existing categories?
) -> None:
    for txn in transactions:  # loop through transactions
        if not overwrite and txn.user_override:  # skip manually edited
            continue  # respect user choices
        if not overwrite and txn.category and txn.category != "Uncategorized":  # skip filled
            continue  # keep category as-is
        suggestion = rules.suggest(txn.description or "")  # get category suggestion
        if suggestion in ("Transfers Out", "Transfers In"):  # handle transfer direction
            desc = (txn.description_raw or "").lower()  # get original lowercase desc
            if "from" in desc and txn.amount > 0:  # incoming funds
                suggestion = "Transfers In"
            elif "to" in desc and txn.amount < 0:  # outgoing funds
                suggestion = "Transfers Out"
        if suggestion:  # apply category if found
            txn.category = suggestion  # assign

def set_category(txn: Transaction, category: str, *, mark_override: bool = True) -> None:
    txn.category = (category or "").strip() or "Uncategorized"  # sanitize + set category
    if mark_override:  # mark manual override
        txn.user_override = True  # prevent auto-overwrite

def set_notes(txn: Transaction, notes: str) -> None:
    txn.notes = (notes or "").strip()[:2048]  # trim to max length and set


# -------------------- dict → Transaction adapter --------------------

def dicts_to_transactions(
    rows: Iterable[dict],  # parsed CSV rows
    *,
    source_bank: Banks | None = None,  # optional bank enum
    source_name: str = "auto-detect",  # name for provenance
    source_upload_id: str = "",  # unique upload tag
    statement_month: str = "",  # user-friendly statement label
    default_currency: str = "USD",  # default currency
) -> List[Transaction]:
    """Convert parsed dict rows into Transaction objects with bank detection."""  # docstring
    out: List[Transaction] = []  # list of Transaction objects
    for i, r in enumerate(rows, start=1):  # enumerate each row
        if not isinstance(r, dict):  # ensure valid dict
            continue  # skip invalid rows

        # ---------- Detect Bank Type ----------
        bank_type = None  # initialize detection
        if source_bank:  # if provided explicitly
            bank_type = source_bank
        else:  # auto-detect via column headers
            keys = {str(k) for k in r.keys()}  # collect keys
            if {"Details", "Posting Date", "Description", "Amount"} <= keys:  # chase
                bank_type = Banks.CHASE
            elif {"Date", "Amount", "Description"} <= keys:  # wells fargo
                bank_type = Banks.WELLS_FARGO
            else:
                bank_type = None  # unknown

        # ---------- Extract Data ----------
        if bank_type == Banks.CHASE:  # Chase layout
            date_str = str(r.get("Posting Date", "")).strip()  # extract date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = str(r.get("Balance", "")).strip() or None  # optional balance
        elif bank_type == Banks.WELLS_FARGO:  # Wells layout
            date_str = str(r.get("Date", "")).strip()  # date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = None  # no balance in file
        else:  # unknown layout fallback
            date_str = str(r.get("Date", "") or r.get("Posting Date", "")).strip()  # pick best
            desc = str(r.get("Description", "") or r.get("Details", "")).strip()  # pick best desc
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = str(r.get("Balance", "")).strip() or None  # optional balance

        # ---------- Parse and Normalize ----------
        date = _parse_date(date_str) or datetime.now()  # parse or default
        amt = _parse_decimal(amt_str) or Decimal("0")  # parse to Decimal
        bal = _parse_decimal(bal_str) if bal_str else None  # parse balance if available
        norm_desc = _normalize_for_match(_strip_boilerplate(desc))  # clean text

        # ---------- Create Transaction ----------
        txn = Transaction(  # build model
            id=f"row:{i}",  # unique synthetic ID
            date=date,  # parsed date
            posted_date=None,  # unused
            description=norm_desc or desc,  # normalized description
            description_raw=desc,  # raw text
            amount=amt,  # transaction amount
            balance=bal,  # account balance (optional)
            txn_type="",  # not used
            currency=default_currency,  # USD default
            category="Uncategorized",  # default category
            notes="",  # empty notes
            user_override=False,  # not user-edited yet
            statement_month=statement_month,  # user label for statement period
            source_name=(source_name if source_name != "auto-detect" else (bank_type.name.lower() if bank_type else "unknown")),
            source_upload_id=source_upload_id,  # upload provenance
            raw=dict(r),  # keep full raw record
        )
        out.append(txn)  # add to output list
    return out  # return Transaction list


# -------------------- value parsing helpers --------------------

def _parse_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val:  # empty guard
        return None
    s = val.replace(",", "").replace("$", "").strip()  # remove commas/$
    if s.startswith("(") and s.endswith(")"):  # accounting negative format
        s = "-" + s[1:-1]  # convert to -value
    try:
        return Decimal(s)  # return Decimal object
    except (InvalidOperation, ValueError):  # invalid number
        return None  # fail silently


def _parse_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()  # clean input
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%b %d %Y", "%d %b %Y"):  # try all formats
        try:
            return datetime.strptime(s, fmt)  # parse successfully
        except ValueError:
            continue  # try next format
    try:
        return datetime.fromisoformat(s)  # try ISO fallback
    except Exception:
        return None  # all failed


# -------------------- description cleaning --------------------

_BOILER_FRAGMENTS = [  # phrases to remove
    "purchase authorized", "purchase auth", "pos purchase",
    "debit card purchase", "debit purchase", "card purchase",
    "signature purchase", "contactless",
    "recurring payment authorized", "recurring payment",
    "authorization", "authorized",
    "atm withdrawal", "non-wf atm", "withdrawal authorized",
    "online transfer", "internal transfer",
    "posted on", "post date",
]

_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.IGNORECASE)  # matches dates
_CARD_RE = re.compile(r"\b(?:card|debit)\s*\d{2,6}\b", re.IGNORECASE)  # matches card tails
_NUMBLOB_RE = re.compile(r"\b\d{6,}\b")  # long number patterns
_SUFFIX_RE = re.compile(r"\b(llc|inc|co|corp|ltd|llp|plc)\b", re.IGNORECASE)  # company suffixes
_SPACE_RE = re.compile(r"\s+")  # multi-space
_PUNCT_RE = re.compile(r"[^a-z0-9\s&'-]+")  # remove punctuation


def _strip_boilerplate(desc: str) -> str:
    s = desc.lower()  # lowercase everything
    for frag in _BOILER_FRAGMENTS:  # remove common noise phrases
        s = s.replace(frag, " ")
    s = _DATE_RE.sub(" ", s)  # remove dates
    s = _CARD_RE.sub(" ", s)  # remove card numbers
    s = _NUMBLOB_RE.sub(" ", s)  # remove long numeric blobs
    return s  # cleaned text


def _normalize_for_match(s: str) -> str:
    s2 = s.lower()  # lower text
    s2 = _PUNCT_RE.sub(" ", s2)  # remove punctuation
    s2 = _SUFFIX_RE.sub(" ", s2)  # remove suffixes
    s2 = _SPACE_RE.sub(" ", s2).strip()  # collapse spaces
    return s2  # normalized text


def _prep_desc_for_rules(raw_desc: str) -> str:
    return _normalize_for_match(_strip_boilerplate(raw_desc or ""))  # full cleanup
