"""
Parse raw API responses from Doffin and TED into ProcurementNotice objects.

TED field codes used here:
  ND  notice number / dossier id
  TI  title (multilingual dict, we prefer 'NOR' then 'ENG')
  DS  short description
  CA  contracting authority name
  TD  notice type code  (cn-standard, can-standard, …)
  PD  publication date  YYYYMMDD
  DL  deadline          YYYYMMDD
  VA  estimated value   {amount, currency}
  PC  CPV codes         list of {code, …}
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Optional

from .models import NoticeType, ProcurementNotice, VENDOR_KEYWORDS, Vendor

# Authority type classification by name patterns
AUTHORITY_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    ("Helseforetak", ["helse", "sykehus", "hospital", "hf ", "rhf "]),
    ("Kommune", ["kommune", "bydel", "municipal"]),
    ("Statsforvaltning", [
        "direktorat", "departement", "statsforvalter", "fylkesmann",
        "tilsyn", "råd", "utvalg", "etaten", "etat", "ombud",
    ]),
    ("Fylkeskommune", ["fylkeskommune"]),
    ("Universiteter og høyskoler", ["universitet", "høyskole", "høgskole", "ntnu", "uio", "uib"]),
    ("Forsvaret og politi", ["forsvar", "politi", "ffi", "nato"]),
    ("Statlig foretak", ["statsforetak", "sf ", " as ", " asa "]),
]


def _parse_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    if isinstance(raw, date):
        return raw
    s = str(raw)[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _parse_value(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace(" ", "").replace(",", ".")
    m = re.search(r"[\d.]+", s)
    if m:
        return float(m.group())
    return None


def _classify_authority(name: str) -> str:
    if not name:
        return "Ukjent"
    lower = name.lower()
    for label, patterns in AUTHORITY_TYPE_PATTERNS:
        if any(p in lower for p in patterns):
            return label
    return "Annet statlig"


def _notice_type(raw: Any) -> NoticeType:
    if not raw:
        return NoticeType.UNKNOWN
    s = str(raw).lower()
    if any(x in s for x in ["award", "tildeling", "kunngjøring om inngått"]):
        return NoticeType.AWARD
    if any(x in s for x in ["prior", "forhånds", "veiledende"]):
        return NoticeType.PRIOR_INFO
    if any(x in s for x in ["contract", "konkurransegrunn", "kunngjøring om konkurranse", "notice"]):
        return NoticeType.CONTRACT
    return NoticeType.UNKNOWN


def _ted_text(field: Any) -> str:
    """TED multilingual fields are dicts like {'NOR': '...', 'ENG': '...'}."""
    if isinstance(field, dict):
        return field.get("NOR") or field.get("ENG") or next(iter(field.values()), "") or ""
    return str(field) if field else ""


def _ted_notice_type(td: str) -> NoticeType:
    td = (td or "").lower()
    if "can" in td or "award" in td:
        return NoticeType.AWARD
    if "pin" in td or "prior" in td:
        return NoticeType.PRIOR_INFO
    if "cn" in td or "contract" in td:
        return NoticeType.CONTRACT
    return NoticeType.UNKNOWN


def _ted_date(raw: Any) -> Optional[date]:
    """TED dates are YYYYMMDD integers or strings."""
    if not raw:
        return None
    s = str(raw).strip()[:8]
    if len(s) == 8 and s.isdigit():
        try:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            pass
    return _parse_date(raw)


def _ted_value_nok(va: Any) -> Optional[float]:
    """VA is {amount: float, currency: str}. Convert EUR→NOK at ~11.5 if needed."""
    if not isinstance(va, dict):
        return None
    amount = va.get("amount") or va.get("value")
    if not amount:
        return None
    currency = (va.get("currency") or "NOK").upper()
    amount = float(amount)
    if currency == "NOK":
        return amount
    if currency == "EUR":
        return amount * 11.5  # approximate NOK/EUR for historical data
    return amount  # leave other currencies as-is (rare for NO notices)


def parse_ted_notice(raw: dict[str, Any]) -> Optional[ProcurementNotice]:
    """Parse a TED v3 API notice into ProcurementNotice."""
    notice_id = str(raw.get("ND") or raw.get("noticeNumber") or "")
    if not notice_id:
        return None

    title = _ted_text(raw.get("TI") or raw.get("title") or "")
    description = _ted_text(raw.get("DS") or raw.get("description") or "")

    ca = raw.get("CA") or raw.get("contractingAuthority") or {}
    authority_name = _ted_text(ca) if isinstance(ca, dict) else str(ca)

    cpv_raw = raw.get("PC") or raw.get("cpvCodes") or []
    cpv_codes = [
        str(c.get("code", c) if isinstance(c, dict) else c)
        for c in (cpv_raw if isinstance(cpv_raw, list) else [cpv_raw])
    ]

    notice = ProcurementNotice(
        notice_id=f"TED-{notice_id}",
        title=title,
        description=description,
        contracting_authority=authority_name,
        authority_type=_classify_authority(authority_name),
        notice_type=_ted_notice_type(str(raw.get("TD") or "")),
        published_date=_ted_date(raw.get("PD") or raw.get("publicationDate")),
        deadline_date=_ted_date(raw.get("DL") or raw.get("deadline")),
        estimated_value_nok=_ted_value_nok(raw.get("VA") or raw.get("estimatedValue")),
        cpv_codes=cpv_codes,
        raw_url=f"https://ted.europa.eu/udl?uri=TED:NOTICE:{notice_id}:TEXT:EN:HTML",
    )
    notice.matched_vendors = notice.detect_vendors()
    return notice


def parse_notice(raw: dict[str, Any], source: str = "doffin") -> Optional[ProcurementNotice]:
    if source == "ted":
        return parse_ted_notice(raw)

    notice_id = str(
        raw.get("id") or raw.get("noticeId") or raw.get("doffinId") or raw.get("referenceNumber", "")
    )
    if not notice_id:
        return None

    title = raw.get("title") or raw.get("name") or raw.get("subject") or ""
    description = (
        raw.get("description")
        or raw.get("shortDescription")
        or raw.get("contractDescription")
        or ""
    )

    authority = (
        raw.get("contractingAuthority")
        or raw.get("buyerName")
        or raw.get("organisation", {}).get("name", "")
        if isinstance(raw.get("organisation"), dict)
        else raw.get("organisation", "")
    )
    authority_name = str(authority) if authority else ""

    cpv_raw = raw.get("cpvCodes") or raw.get("cpv") or []
    if isinstance(cpv_raw, list):
        cpv_codes = [str(c.get("code", c) if isinstance(c, dict) else c) for c in cpv_raw]
    else:
        cpv_codes = [str(cpv_raw)] if cpv_raw else []

    notice = ProcurementNotice(
        notice_id=notice_id,
        title=title,
        description=description,
        contracting_authority=authority_name,
        authority_type=_classify_authority(authority_name),
        notice_type=_notice_type(raw.get("noticeType") or raw.get("type") or raw.get("formType")),
        published_date=_parse_date(raw.get("publishedDate") or raw.get("publishDate") or raw.get("publicationDate")),
        deadline_date=_parse_date(raw.get("deadline") or raw.get("submissionDeadline")),
        estimated_value_nok=_parse_value(raw.get("estimatedValue") or raw.get("totalValue") or raw.get("value")),
        cpv_codes=cpv_codes,
        raw_url=raw.get("url") or raw.get("link") or f"https://doffin.no/Notice/Details/{notice_id}",
    )
    notice.matched_vendors = notice.detect_vendors()
    return notice
