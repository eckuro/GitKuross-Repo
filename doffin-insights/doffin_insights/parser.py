"""Parse raw Doffin API responses into ProcurementNotice objects."""
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


def parse_notice(raw: dict[str, Any]) -> Optional[ProcurementNotice]:
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
