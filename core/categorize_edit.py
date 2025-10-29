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
* This module expects list[Transaction]. Convert dicts -> Transaction upstream.
"""

from __future__ import annotations  # future annotations for simpler type hints

import json  # load/save JSON rules
import re  # regex matching and cleanup
from datetime import datetime  # parse/hold dates
from decimal import Decimal, InvalidOperation  # money-safe numbers
from pathlib import Path  # filesystem paths
from typing import Dict, Iterable, List, Optional, Sequence, Tuple  # typing helpers

from core.models import Transaction  # single source of truth for the model


# -------------------- rules engine --------------------

class CategoryRules:  # container for compiled category patterns
    # JSON example:
    # { "Groceries": ["kroger", "walmart"], "Dining": ["starbucks", "re:.*pizza.*"] }
    def __init__(self, compiled: List[Tuple[str, List[re.Pattern]]]):  # ctor takes precompiled map
        self._compiled = compiled  # store category -> patterns list

    @classmethod
    def from_json(cls, path: Path) -> "CategoryRules":  # build rules from a JSON file
        data = json.loads(Path(path).read_text(encoding="utf-8"))  # read+parse json
        if not isinstance(data, dict):  # validate top-level structure
            raise ValueError("rules.json must be an object of {category: [patterns...]}")  # clear error
        compiled: List[Tuple[str, List[re.Pattern]]] = []  # accumulator for compiled patterns
        for category, patterns in data.items():  # dict keeps insertion order
            if not isinstance(patterns, Sequence):  # each category must map to a list
                raise ValueError(f"Category '{category}' must map to a list of patterns.")  # guard
            bucket: List[re.Pattern] = []  # hold compiled patterns for this category
            for p in patterns:  # iterate raw patterns
                if not isinstance(p, str):  # pattern must be string
                    raise ValueError(f"Pattern in '{category}' must be a string.")  # guard
                if p.startswith("re:"):  # regex pattern path
                    bucket.append(re.compile(p[3:], re.IGNORECASE))  # compile regex (case-insensitive)
                else:
                    bucket.append(re.compile(re.escape(p), re.IGNORECASE))  # compile substring match
            compiled.append((category, bucket))  # keep pair in order
        return cls(compiled)  # return rules instance

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "CategoryRules":  # convenience for inline dicts
        tmp = Path("__inline_rules__.json")  # temp path for reuse of from_json
        tmp.write_text(json.dumps(data), encoding="utf-8")  # write dict to disk
        try:
            return cls.from_json(tmp)  # reuse json loader
        finally:
            try:
                tmp.unlink()  # clean temp file
            except Exception:
                pass  # ignore cleanup errors

    def suggest(self, description: str) -> Optional[str]:  # pick first matching category
        text = _prep_desc_for_rules(description)  # clean/normalize description
        for category, patterns in self._compiled:  # iterate categories in order
            for pat in patterns:  # try each pattern
                if pat.search(text):  # on match
                    return category  # return the category immediately
        return None  # no match found


# -------------------- public api: transactions only --------------------

def auto_categorize(
    transactions: Iterable[Transaction],  # list of Transaction objects
    rules: CategoryRules,  # compiled rules to use
    *,
    overwrite: bool = False,  # if True, replace existing categories
) -> None:
    # overwrite=False: keep user_override and any non-empty category
    for txn in transactions:  # iterate all transactions
        if not overwrite and txn.user_override:  # respect manual override
            continue  # skip changes
        if not overwrite and txn.category and txn.category != "Uncategorized":  # keep existing category
            continue  # skip changes
        suggestion = rules.suggest(txn.description or "")  # get suggested category
        if suggestion:  # if we have a match
            txn.category = suggestion  # apply category


def set_category(txn: Transaction, category: str, *, mark_override: bool = True) -> None:  # manual set
    txn.category = (category or "").strip() or "Uncategorized"  # sanitize/assign category
    if mark_override:  # mark as user override if requested
        txn.user_override = True  # prevent later overwrites


def set_notes(txn: Transaction, notes: str) -> None:  # attach or update notes
    txn.notes = (notes or "").strip()[:2048]  # trim and cap length


# -------------------- adapter kept for upstream conversion --------------------
# Use this in your ingest pipeline *before* calling auto_categorize.

_DEFAULT_MAP = {  # common column name guesses from various exports
    "id": ["Id", "ID", "TransactionId", "Ref", "Reference"],  # identifiers
    "date": ["Date", "Transaction Date", "Posted Date", "Posting Date"],  # primary date
    "posted_date": ["Posted Date", "Posting Date"],  # posted/settled date
    "description": ["Description", "Memo", "Details", "Name"],  # human description
    "amount": ["Amount", "Transaction Amount", "Value"],  # signed amount
    "debit": ["Debit", "Withdrawal", "Outflow"],  # separate debit column
    "credit": ["Credit", "Deposit", "Inflow"],  # separate credit column
    "balance": ["Balance", "Running Balance"],  # running balance if present
    "type": ["Type", "Transaction Type", "Category"],  # bank's own type/category
    "currency": ["Currency", "CCY"],  # currency code
}  # end map

_DATE_FORMATS = [  # date formats to try when parsing
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y",
    "%b %d %Y", "%d %b %Y",
]  # common formats


def dicts_to_transactions(
    rows: Iterable[dict],  # raw rows from CSV/parser
    *,
    source_name: str = "unknown",  # provenance: bank/source name
    source_upload_id: str = "",  # link to this upload
    statement_month: str = "",  # user-friendly statement label
    field_map: Dict[str, List[str]] | None = None,  # optional custom column map
    default_currency: str = "USD",  # fallback currency
) -> List[Transaction]:
    # field_map lets us override/extend _DEFAULT_MAP per parser if needed
    fmap = {**_DEFAULT_MAP, **(field_map or {})}  # merge defaults with overrides
    out: List[Transaction] = []  # accumulator for Transactions

    for i, r in enumerate(rows, start=1):  # iterate each dict row
        if not isinstance(r, dict):  # guard for bad input
            continue  # skip non-dicts

        rid = _pick_first(r, fmap["id"]) or f"row:{i}"  # choose id or synthesize
        amt = _parse_amount(r, fmap)  # compute signed amount

        raw_desc = _pick_first(r, fmap["description"]) or ""  # pull original description
        norm_desc = _normalize_for_match(_strip_boilerplate(raw_desc))  # normalized form

        date_str = _pick_first(r, fmap["date"]) or ""  # choose primary date field
        date = _parse_date(date_str) or datetime.now()  # parse or fallback to now
        posted_str = _pick_first(r, fmap["posted_date"]) or ""  # choose posted date field
        posted = _parse_date(posted_str) if posted_str else None  # parse posted date

        bal = _parse_decimal(_pick_first(r, fmap["balance"]))  # optional running balance
        txn_type = (_pick_first(r, fmap["type"]) or "").strip()  # bank's type/category
        currency = (_pick_first(r, fmap["currency"]) or default_currency).strip().upper()  # currency code

        txn = Transaction(  # build normalized Transaction
            id=str(rid),  # final id string
            date=date,  # primary date
            posted_date=posted,  # posted/settled date if present
            description=norm_desc or (raw_desc.strip()),  # normalized desc, fallback to raw
            description_raw=raw_desc.strip(),  # store original description
            amount=amt,  # signed amount
            balance=bal,  # running balance (optional)
            txn_type=txn_type,  # bank type/category
            currency=currency or default_currency,  # final currency
            category="Uncategorized",  # initial category
            notes="",  # empty notes
            user_override=False,  # not manually set yet
            statement_month=statement_month,  # user label for statement period
            source_name=source_name,  # provenance: bank/source
            source_upload_id=source_upload_id,  # provenance: upload id
            raw=dict(r),  # keep full original row
        )
        out.append(txn)  # collect

    return out  # list of Transactions


def _pick_first(row: dict, candidates: List[str]) -> Optional[str]:  # pick first non-empty column
    for c in candidates:  # iterate candidate names
        if c in row and str(row[c]).strip():  # if present and not blank
            return str(row[c]).strip()  # return cleaned string
    return None  # nothing found


def _parse_amount(row: dict, fmap: Dict[str, List[str]]) -> Decimal:  # derive signed amount
    val = _pick_first(row, fmap["amount"])  # try single Amount column first
    if val is not None:  # if present
        dec = _parse_decimal(val)  # convert to Decimal
        if dec is not None:  # if valid number
            return dec  # return as-is (already signed if export is signed)
    debit = _pick_first(row, fmap["debit"])  # try Debit column
    credit = _pick_first(row, fmap["credit"])  # try Credit column
    if debit:  # debit found
        d = _parse_decimal(debit) or Decimal("0")  # parse or zero
        return -abs(d)  # ensure negative spend
    if credit:  # credit found
        c = _parse_decimal(credit) or Decimal("0")  # parse or zero
        return abs(c)  # ensure positive income
    return Decimal("0")  # fallback zero


def _parse_decimal(val: Optional[str]) -> Optional[Decimal]:  # safe decimal parser
    if not val:  # empty guard
        return None  # no value
    s = val.replace(",", "").replace("$", "").strip()  # strip formatting
    if s.startswith("(") and s.endswith(")"):  # accounting negative (parentheses)
        s = "-" + s[1:-1]  # convert to -value
    try:
        return Decimal(s)  # build Decimal
    except (InvalidOperation, ValueError):  # invalid number
        return None  # signal parse failure


def _parse_date(s: str) -> Optional[datetime]:  # try multiple date formats
    s = (s or "").strip()  # clean input
    for fmt in _DATE_FORMATS:  # iterate known formats
        try:
            return datetime.strptime(s, fmt)  # parse with format
        except ValueError:
            continue  # try next format
    try:
        return datetime.fromisoformat(s)  # last resort ISO-ish
    except Exception:
        return None  # give up


# -------------------- description cleaning --------------------

_BOILER_FRAGMENTS = [  # noisy phrases to strip before matching
    "purchase authorized", "purchase auth", "pos purchase",
    "debit card purchase", "debit purchase", "card purchase",
    "signature purchase", "contactless",
    "recurring payment authorized", "recurring payment",
    "authorization", "authorized",
    "atm withdrawal", "non-wf atm", "withdrawal authorized",
    "online transfer", "internal transfer",
    "posted on", "post date",
]  # end list

_DATE_RE    = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.IGNORECASE)  # dates like 09/15/2025
_CARD_RE    = re.compile(r"\b(?:card|debit)\s*\d{2,6}\b", re.IGNORECASE)  # card tails like "card 6627"
_NUMBLOB_RE = re.compile(r"\b\d{6,}\b")  # long numeric blobs (auth/trace)
_SUFFIX_RE  = re.compile(r"\b(llc|inc|co|corp|ltd|llp|plc)\b", re.IGNORECASE)  # company suffixes
_SPACE_RE   = re.compile(r"\s+")  # whitespace collapsing
_PUNCT_RE   = re.compile(r"[^a-z0-9\s&'-]+")  # remove most punctuation

def _strip_boilerplate(desc: str) -> str:  # remove bank noise before normalize
    s = desc.lower()  # lowercase first
    for frag in _BOILER_FRAGMENTS:  # remove known boilerplate fragments
        s = s.replace(frag, " ")  # replace with space
    s = _DATE_RE.sub(" ", s)  # drop date tokens
    s = _CARD_RE.sub(" ", s)  # drop card tails
    s = _NUMBLOB_RE.sub(" ", s)  # drop long numbers
    return s  # partially cleaned string

def _normalize_for_match(s: str) -> str:  # normalize for stable matching
    s2 = s.lower()  # lower for case-insensitivity
    s2 = _PUNCT_RE.sub(" ", s2)  # remove punctuation except & ' -
    s2 = _SUFFIX_RE.sub(" ", s2)  # remove company suffixes
    s2 = _SPACE_RE.sub(" ", s2).strip()  # collapse spaces
    return s2  # final normalized text

def _prep_desc_for_rules(raw_desc: str) -> str:  # full cleaning pipeline
    return _normalize_for_match(_strip_boilerplate(raw_desc or ""))  # strip then normalize


# -------------------- tiny CLI --------------------

def _cli(argv: List[str]) -> int:  # small CLI to test a single description
    import argparse  # local import to keep top clean
    p = argparse.ArgumentParser(description="Suggest a category for a description using rules.json")  # parser
    p.add_argument("rules", type=Path, help="Path to rules.json")  # rules file path
    p.add_argument("--desc", required=True, help="Transaction description to test")  # description arg
    args = p.parse_args(argv)  # parse args

    rules = CategoryRules.from_json(args.rules)  # load rules
    cat = rules.suggest(args.desc)  # get category suggestion
    print(cat or "Uncategorized")  # output result
    return 0  # success code


if __name__ == "__main__":  # run as script
    import sys as _sys  # alias sys
    raise SystemExit(_cli(_sys.argv[1:]))  # exit with CLI status
