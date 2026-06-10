"""Tests for the notice parser and vendor keyword matching."""
import pytest
from doffin_insights.models import ProcurementNotice, NoticeType
from doffin_insights.parser import parse_notice, _classify_authority


def test_parse_basic_notice():
    raw = {
        "id": "2024-001",
        "title": "Anskaffelse av SAP S/4HANA ERP-system",
        "description": "Implementering og drift av SAP løsning",
        "contractingAuthority": "Oslo kommune",
        "noticeType": "contract_notice",
        "publishedDate": "2024-03-15",
        "estimatedValue": 5000000,
    }
    notice = parse_notice(raw)
    assert notice is not None
    assert notice.notice_id == "2024-001"
    assert "SAP" in notice.matched_vendors
    assert notice.estimated_value_nok == 5_000_000.0
    assert notice.published_date.year == 2024


def test_vendor_detection_dynamics():
    n = ProcurementNotice(
        notice_id="x",
        title="Microsoft Dynamics 365 Business Central implementering",
    )
    vendors = n.detect_vendors()
    assert "Microsoft Dynamics" in vendors


def test_vendor_detection_servicenow():
    n = ProcurementNotice(
        notice_id="x",
        title="ITSM-system basert på ServiceNow plattform",
    )
    assert "ServiceNow" in n.detect_vendors()


def test_vendor_detection_ifs():
    n = ProcurementNotice(
        notice_id="x",
        title="Anskaffelse av ERP IFS Applications",
        description="Virksomheten ønsker å anskaffe IFS cloud.",
    )
    assert "IFS" in n.detect_vendors()


def test_no_vendor_match():
    n = ProcurementNotice(
        notice_id="x",
        title="Renholdstjenester for kommunale bygg",
    )
    assert n.detect_vendors() == []


def test_classify_authority_kommune():
    assert _classify_authority("Trondheim kommune") == "Kommune"


def test_classify_authority_health():
    assert _classify_authority("Oslo universitetssykehus HF") == "Helseforetak"


def test_classify_authority_university():
    assert _classify_authority("Universitetet i Bergen") == "Universiteter og høyskoler"


def test_parse_missing_id_returns_none():
    assert parse_notice({}) is None
