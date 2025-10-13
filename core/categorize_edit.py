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

from __future__ import annotations  # future-proof type hints

import json  # load/save JSON data
import re  # regex handling
from datetime import datetime  # date parsing
from decimal import Decimal, InvalidOperation  # precise money handling
from pathlib import Path  # filesystem paths
from typing import Dict, Iterable, List, Optional, Sequence, Tuple  # type hints

from core.models import Transaction  # unified transaction model
from fileUpload.fileUpload import Banks  # enum for source bank


# -------------------- rules engine --------------------

class CategoryRules:
    def __init__(self, compiled: List[Tuple[str, List[re.Pattern]]]):  # constructor with precompiled rules
        self._compiled = compiled  # store category-pattern pairs

    @classmethod
    def from_json(cls, path: Path) -> "CategoryRules":  # load rules from JSON
        data = json.loads(Path(path).read_text(encoding="utf-8"))  # read JSON
        if not isinstance(data, dict):  # ensure structure is valid
            raise ValueError("rules.json must be an object of {category: [patterns...]}")  # raise if invalid
        compiled: List[Tuple[str, List[re.Pattern]]] = []  # hold compiled patterns
        for category, patterns in data.items():  # iterate over categories
            if not isinstance(patterns, Sequence):  # must be list-like
                raise ValueError(f"Category '{category}' must map to a list of patterns.")  # error if not
            bucket: List[re.Pattern] = []  # collect regex objects
            for p in patterns:  # loop through each pattern
                if not isinstance(p, str):  # must be string
                    raise ValueError(f"Pattern in '{category}' must be a string.")  # fail if not
                if p.startswith("re:"):  # if regex syntax
                    bucket.append(re.compile(p[3:], re.IGNORECASE))  # compile regex
                else:
                    bucket.append(re.compile(re.escape(p), re.IGNORECASE))  # compile literal substring
            compiled.append((category, bucket))  # add category + patterns
        return cls(compiled)  # return instance

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "CategoryRules":  # alt constructor from dict
        tmp = Path("__inline_rules__.json")  # temporary file path
        tmp.write_text(json.dumps(data), encoding="utf-8")  # write dict as JSON
        try:
            return cls.from_json(tmp)  # reuse JSON loader
        finally:
            try:
                tmp.unlink()  # delete temp file
            except Exception:
                pass  # ignore cleanup errors

    def suggest(self, description: str) -> Optional[str]:  # return category match for description
        text = _prep_desc_for_rules(description)  # normalize input
        for category, patterns in self._compiled:  # go through rules
            for pat in patterns:  # check each pattern
                if pat.search(text):  # if found
                    return category  # return category
        return None  # fallback if no match


# -------------------- public API --------------------

def auto_categorize(
    transactions: Iterable[Transaction],  # list of transactions
    rules: CategoryRules,  # rule engine instance
    *,
    overwrite: bool = False,  # avoid overwriting manual edits
) -> None:
    for txn in transactions:  # loop through transactions
        if not overwrite and txn.user_override:  # skip manual overrides
            continue
        if not overwrite and txn.category and txn.category != "Uncategorized":  # skip already set
            continue

        suggestion = rules.suggest(txn.description or "")  # get rule suggestion

        if suggestion in ("Transfers Out", "Transfers In"):  # if transfer-related
            desc = (txn.description_raw or "").lower()  # lower-case desc
            if "from" in desc and txn.amount > 0:  # incoming transfer
                suggestion = "Transfers In"
            elif "to" in desc and txn.amount < 0:  # outgoing transfer
                suggestion = "Transfers Out"

        if suggestion:  # if found
            txn.category = suggestion  # apply category


def set_category(txn: Transaction, category: str, *, mark_override: bool = True) -> None:  # manually assign category
    txn.category = (category or "").strip() or "Uncategorized"  # clean and assign
    if mark_override:  # optional override flag
        txn.user_override = True  # mark as user-edited


def set_notes(txn: Transaction, notes: str) -> None:  # attach custom notes
    txn.notes = (notes or "").strip()[:2048]  # trim and cap notes length


# -------------------- dict → Transaction adapter --------------------

def dicts_to_transactions(
    rows: Iterable[dict],  # list of raw CSV dicts
    *,
    source_bank: Banks | None = None,  # bank type from enum
    source_name: str = "auto-detect",  # default tag
    source_upload_id: str = "",  # upload tracking ID
    default_currency: str = "USD",  # currency fallback
) -> List[Transaction]:
    out: List[Transaction] = []  # results list

    for i, r in enumerate(rows, start=1):  # iterate rows
        if not isinstance(r, dict):  # skip invalid rows
            continue

        bank_type = None  # default bank
        if source_bank:  # if provided
            bank_type = source_bank  # use directly
        else:  # otherwise infer from headers
            keys = {str(k) for k in r.keys()}  # get headers
            if {"Details", "Posting Date", "Description", "Amount"} <= keys:  # Chase
                bank_type = Banks.CHASE
            elif {"Date", "Amount", "Description"} <= keys:  # Wells Fargo
                bank_type = Banks.WELLS_FARGO
            else:
                bank_type = None  # unknown

        if bank_type == Banks.CHASE:  # Chase format
            date_str = str(r.get("Posting Date", "")).strip()  # date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = str(r.get("Balance", "")).strip() or None  # balance if any
        elif bank_type == Banks.WELLS_FARGO:  # Wells Fargo format
            date_str = str(r.get("Date", "")).strip()  # date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = None  # no balance in WF
        else:  # unknown fallback
            date_str = str(r.get("Date", "") or r.get("Posting Date", "")).strip()  # detect any date
            desc = str(r.get("Description", "") or r.get("Details", "")).strip()  # detect any desc
            amt_str = str(r.get("Amount", "")).strip()  # amount fallback
            bal_str = str(r.get("Balance", "")).strip() or None  # optional balance

        date = _parse_date(date_str) or datetime.now()  # parse date safely
        amt = _parse_decimal(amt_str) or Decimal("0")  # parse amount safely
        bal = _parse_decimal(bal_str) if bal_str else None  # parse balance if present

        norm_desc = _normalize_for_match(_strip_boilerplate(desc))  # normalize desc for rule matching

        txn = Transaction(  # create unified Transaction
            id=f"row:{i}",  # unique row id
            date=date,  # parsed date
            posted_date=None,  # unused for now
            description=norm_desc or desc,  # normalized description
            description_raw=desc,  # original desc
            amount=amt,  # parsed amount
            balance=bal,  # parsed balance
            txn_type="",  # ignore type field
            currency=default_currency,  # default USD
            category="Uncategorized",  # placeholder
            notes="",  # no notes yet
            user_override=False,  # not user-edited
            source_name=(bank_type.name.lower() if bank_type else "unknown"),  # bank name tag
            source_upload_id=source_upload_id,  # upload link
            raw=dict(r),  # original data snapshot
        )
        out.append(txn)  # store transaction

    return out  # return list


# -------------------- value parsing helpers --------------------

def _parse_decimal(val: Optional[str]) -> Optional[Decimal]:  # safely convert string to Decimal
    if not val:
        return None
    s = val.replace(",", "").replace("$", "").strip()  # strip symbols
    if s.startswith("(") and s.endswith(")"):  # handle parentheses negatives
        s = "-" + s[1:-1]
    try:
        return Decimal(s)  # convert to Decimal
    except (InvalidOperation, ValueError):
        return None  # fail gracefully


def _parse_date(s: str) -> Optional[datetime]:  # convert string to datetime
    s = (s or "").strip()  # trim input
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%b %d %Y", "%d %b %Y"):  # try formats
        try:
            return datetime.strptime(s, fmt)  # parse
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)  # ISO fallback
    except Exception:
        return None  # fail silently


# -------------------- description cleaning --------------------

_BOILER_FRAGMENTS = [  # known filler phrases
    "purchase authorized", "purchase auth", "pos purchase",
    "debit card purchase", "debit purchase", "card purchase",
    "signature purchase", "contactless",
    "recurring payment authorized", "recurring payment",
    "authorization", "authorized",
    "atm withdrawal", "non-wf atm", "withdrawal authorized",
    "online transfer", "internal transfer",
    "posted on", "post date",
]

_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.IGNORECASE)  # find date-like text
_CARD_RE = re.compile(r"\b(?:card|debit)\s*\d{2,6}\b", re.IGNORECASE)  # card endings
_NUMBLOB_RE = re.compile(r"\b\d{6,}\b")  # long numeric blobs
_SUFFIX_RE = re.compile(r"\b(llc|inc|co|corp|ltd|llp|plc)\b", re.IGNORECASE)  # business suffix
_SPACE_RE = re.compile(r"\s+")  # whitespace regex
_PUNCT_RE = re.compile(r"[^a-z0-9\s&'-]+")  # punctuation cleanup


def _strip_boilerplate(desc: str) -> str:  # remove boilerplate phrases
    s = desc.lower()
    for frag in _BOILER_FRAGMENTS:
        s = s.replace(frag, " ")
    s = _DATE_RE.sub(" ", s)
    s = _CARD_RE.sub(" ", s)
    s = _NUMBLOB_RE.sub(" ", s)
    return s


def _normalize_for_match(s: str) -> str:  # prepare description for rule match
    s2 = s.lower()
    s2 = _PUNCT_RE.sub(" ", s2)
    s2 = _SUFFIX_RE.sub(" ", s2)
    s2 = _SPACE_RE.sub(" ", s2).strip()
    return s2


def _prep_desc_for_rules(raw_desc: str) -> str:  # full clean pipeline
    return _normalize_for_match(_strip_boilerplate(raw_desc or ""))


# -------------------- tiny CLI --------------------

def _cli(argv: List[str]) -> int:  # quick command-line test tool
    import argparse  # argument parsing
    p = argparse.ArgumentParser(description="Suggest a category for a description using rules.json")  # CLI help
    p.add_argument("rules", type=Path, help="Path to rules.json")  # path argument
    p.add_argument("--desc", required=True, help="Transaction description to test")  # desc argument
    args = p.parse_args(argv)  # parse args

    rules = CategoryRules.from_json(args.rules)  # load rules
    cat = rules.suggest(args.desc)  # suggest category
    print(cat or "Uncategorized")  # output category
    return 0  # success exit code


if __name__ == "__main__":  # run when executed directly
    import sys as _sys  # import sys
    raise SystemExit(_cli(_sys.argv[1:]))  # run CLI
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

from __future__ import annotations  # future-proof type hints

import json  # load/save JSON data
import re  # regex handling
from datetime import datetime  # date parsing
from decimal import Decimal, InvalidOperation  # precise money handling
from pathlib import Path  # filesystem paths
from typing import Dict, Iterable, List, Optional, Sequence, Tuple  # type hints

from core.models import Transaction  # unified transaction model
from fileUpload.fileUpload import Banks  # enum for source bank


# -------------------- rules engine --------------------

class CategoryRules:
    def __init__(self, compiled: List[Tuple[str, List[re.Pattern]]]):  # constructor with precompiled rules
        self._compiled = compiled  # store category-pattern pairs

    @classmethod
    def from_json(cls, path: Path) -> "CategoryRules":  # load rules from JSON
        data = json.loads(Path(path).read_text(encoding="utf-8"))  # read JSON
        if not isinstance(data, dict):  # ensure structure is valid
            raise ValueError("rules.json must be an object of {category: [patterns...]}")  # raise if invalid
        compiled: List[Tuple[str, List[re.Pattern]]] = []  # hold compiled patterns
        for category, patterns in data.items():  # iterate over categories
            if not isinstance(patterns, Sequence):  # must be list-like
                raise ValueError(f"Category '{category}' must map to a list of patterns.")  # error if not
            bucket: List[re.Pattern] = []  # collect regex objects
            for p in patterns:  # loop through each pattern
                if not isinstance(p, str):  # must be string
                    raise ValueError(f"Pattern in '{category}' must be a string.")  # fail if not
                if p.startswith("re:"):  # if regex syntax
                    bucket.append(re.compile(p[3:], re.IGNORECASE))  # compile regex
                else:
                    bucket.append(re.compile(re.escape(p), re.IGNORECASE))  # compile literal substring
            compiled.append((category, bucket))  # add category + patterns
        return cls(compiled)  # return instance

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "CategoryRules":  # alt constructor from dict
        tmp = Path("__inline_rules__.json")  # temporary file path
        tmp.write_text(json.dumps(data), encoding="utf-8")  # write dict as JSON
        try:
            return cls.from_json(tmp)  # reuse JSON loader
        finally:
            try:
                tmp.unlink()  # delete temp file
            except Exception:
                pass  # ignore cleanup errors

    def suggest(self, description: str) -> Optional[str]:  # return category match for description
        text = _prep_desc_for_rules(description)  # normalize input
        for category, patterns in self._compiled:  # go through rules
            for pat in patterns:  # check each pattern
                if pat.search(text):  # if found
                    return category  # return category
        return None  # fallback if no match


# -------------------- public API --------------------

def auto_categorize(
    transactions: Iterable[Transaction],  # list of transactions
    rules: CategoryRules,  # rule engine instance
    *,
    overwrite: bool = False,  # avoid overwriting manual edits
) -> None:
    for txn in transactions:  # loop through transactions
        if not overwrite and txn.user_override:  # skip manual overrides
            continue
        if not overwrite and txn.category and txn.category != "Uncategorized":  # skip already set
            continue

        suggestion = rules.suggest(txn.description or "")  # get rule suggestion

        if suggestion in ("Transfers Out", "Transfers In"):  # if transfer-related
            desc = (txn.description_raw or "").lower()  # lower-case desc
            if "from" in desc and txn.amount > 0:  # incoming transfer
                suggestion = "Transfers In"
            elif "to" in desc and txn.amount < 0:  # outgoing transfer
                suggestion = "Transfers Out"

        if suggestion:  # if found
            txn.category = suggestion  # apply category


def set_category(txn: Transaction, category: str, *, mark_override: bool = True) -> None:  # manually assign category
    txn.category = (category or "").strip() or "Uncategorized"  # clean and assign
    if mark_override:  # optional override flag
        txn.user_override = True  # mark as user-edited


def set_notes(txn: Transaction, notes: str) -> None:  # attach custom notes
    txn.notes = (notes or "").strip()[:2048]  # trim and cap notes length


# -------------------- dict → Transaction adapter --------------------

def dicts_to_transactions(
    rows: Iterable[dict],  # list of raw CSV dicts
    *,
    source_bank: Banks | None = None,  # bank type from enum
    source_name: str = "auto-detect",  # default tag
    source_upload_id: str = "",  # upload tracking ID
    default_currency: str = "USD",  # currency fallback
) -> List[Transaction]:
    out: List[Transaction] = []  # results list

    for i, r in enumerate(rows, start=1):  # iterate rows
        if not isinstance(r, dict):  # skip invalid rows
            continue

        bank_type = None  # default bank
        if source_bank:  # if provided
            bank_type = source_bank  # use directly
        else:  # otherwise infer from headers
            keys = {str(k) for k in r.keys()}  # get headers
            if {"Details", "Posting Date", "Description", "Amount"} <= keys:  # Chase
                bank_type = Banks.CHASE
            elif {"Date", "Amount", "Description"} <= keys:  # Wells Fargo
                bank_type = Banks.WELLS_FARGO
            else:
                bank_type = None  # unknown

        if bank_type == Banks.CHASE:  # Chase format
            date_str = str(r.get("Posting Date", "")).strip()  # date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = str(r.get("Balance", "")).strip() or None  # balance if any
        elif bank_type == Banks.WELLS_FARGO:  # Wells Fargo format
            date_str = str(r.get("Date", "")).strip()  # date
            desc = str(r.get("Description", "")).strip()  # description
            amt_str = str(r.get("Amount", "")).strip()  # amount
            bal_str = None  # no balance in WF
        else:  # unknown fallback
            date_str = str(r.get("Date", "") or r.get("Posting Date", "")).strip()  # detect any date
            desc = str(r.get("Description", "") or r.get("Details", "")).strip()  # detect any desc
            amt_str = str(r.get("Amount", "")).strip()  # amount fallback
            bal_str = str(r.get("Balance", "")).strip() or None  # optional balance

        date = _parse_date(date_str) or datetime.now()  # parse date safely
        amt = _parse_decimal(amt_str) or Decimal("0")  # parse amount safely
        bal = _parse_decimal(bal_str) if bal_str else None  # parse balance if present

        norm_desc = _normalize_for_match(_strip_boilerplate(desc))  # normalize desc for rule matching

        txn = Transaction(  # create unified Transaction
            id=f"row:{i}",  # unique row id
            date=date,  # parsed date
            posted_date=None,  # unused for now
            description=norm_desc or desc,  # normalized description
            description_raw=desc,  # original desc
            amount=amt,  # parsed amount
            balance=bal,  # parsed balance
            txn_type="",  # ignore type field
            currency=default_currency,  # default USD
            category="Uncategorized",  # placeholder
            notes="",  # no notes yet
            user_override=False,  # not user-edited
            source_name=(bank_type.name.lower() if bank_type else "unknown"),  # bank name tag
            source_upload_id=source_upload_id,  # upload link
            raw=dict(r),  # original data snapshot
        )
        out.append(txn)  # store transaction

    return out  # return list


# -------------------- value parsing helpers --------------------

def _parse_decimal(val: Optional[str]) -> Optional[Decimal]:  # safely convert string to Decimal
    if not val:
        return None
    s = val.replace(",", "").replace("$", "").strip()  # strip symbols
    if s.startswith("(") and s.endswith(")"):  # handle parentheses negatives
        s = "-" + s[1:-1]
    try:
        return Decimal(s)  # convert to Decimal
    except (InvalidOperation, ValueError):
        return None  # fail gracefully


def _parse_date(s: str) -> Optional[datetime]:  # convert string to datetime
    s = (s or "").strip()  # trim input
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%b %d %Y", "%d %b %Y"):  # try formats
        try:
            return datetime.strptime(s, fmt)  # parse
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)  # ISO fallback
    except Exception:
        return None  # fail silently


# -------------------- description cleaning --------------------

_BOILER_FRAGMENTS = [  # known filler phrases
    "purchase authorized", "purchase auth", "pos purchase",
    "debit card purchase", "debit purchase", "card purchase",
    "signature purchase", "contactless",
    "recurring payment authorized", "recurring payment",
    "authorization", "authorized",
    "atm withdrawal", "non-wf atm", "withdrawal authorized",
    "online transfer", "internal transfer",
    "posted on", "post date",
]

_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.IGNORECASE)  # find date-like text
_CARD_RE = re.compile(r"\b(?:card|debit)\s*\d{2,6}\b", re.IGNORECASE)  # card endings
_NUMBLOB_RE = re.compile(r"\b\d{6,}\b")  # long numeric blobs
_SUFFIX_RE = re.compile(r"\b(llc|inc|co|corp|ltd|llp|plc)\b", re.IGNORECASE)  # business suffix
_SPACE_RE = re.compile(r"\s+")  # whitespace regex
_PUNCT_RE = re.compile(r"[^a-z0-9\s&'-]+")  # punctuation cleanup


def _strip_boilerplate(desc: str) -> str:  # remove boilerplate phrases
    s = desc.lower()
    for frag in _BOILER_FRAGMENTS:
        s = s.replace(frag, " ")
    s = _DATE_RE.sub(" ", s)
    s = _CARD_RE.sub(" ", s)
    s = _NUMBLOB_RE.sub(" ", s)
    return s


def _normalize_for_match(s: str) -> str:  # prepare description for rule match
    s2 = s.lower()
    s2 = _PUNCT_RE.sub(" ", s2)
    s2 = _SUFFIX_RE.sub(" ", s2)
    s2 = _SPACE_RE.sub(" ", s2).strip()
    return s2


def _prep_desc_for_rules(raw_desc: str) -> str:  # full clean pipeline
    return _normalize_for_match(_strip_boilerplate(raw_desc or ""))


# -------------------- tiny CLI --------------------

def _cli(argv: List[str]) -> int:  # quick command-line test tool
    import argparse  # argument parsing
    p = argparse.ArgumentParser(description="Suggest a category for a description using rules.json")  # CLI help
    p.add_argument("rules", type=Path, help="Path to rules.json")  # path argument
    p.add_argument("--desc", required=True, help="Transaction description to test")  # desc argument
    args = p.parse_args(argv)  # parse args

    rules = CategoryRules.from_json(args.rules)  # load rules
    cat = rules.suggest(args.desc)  # suggest category
    print(cat or "Uncategorized")  # output category
    return 0  # success exit code


if __name__ == "__main__":  # run when executed directly
    import sys as _sys  # import sys
    raise SystemExit(_cli(_sys.argv[1:]))  # run CLI
