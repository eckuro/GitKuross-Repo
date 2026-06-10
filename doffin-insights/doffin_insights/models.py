from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NoticeType(str, Enum):
    PRIOR_INFO = "prior_information"
    CONTRACT = "contract_notice"
    AWARD = "contract_award"
    UNKNOWN = "unknown"


class Vendor(str, Enum):
    DYNAMICS = "Microsoft Dynamics"
    SAP = "SAP"
    SERVICENOW = "ServiceNow"
    ORACLE = "Oracle"
    IFS = "IFS"
    SALESFORCE = "Salesforce"
    WORKDAY = "Workday"


VENDOR_KEYWORDS: dict[Vendor, list[str]] = {
    Vendor.DYNAMICS: [
        "dynamics 365", "microsoft dynamics", "d365", "dynamics crm",
        "dynamics erp", "dynamics ax", "dynamics nav", "dynamics bc",
        "business central", "dynamics fo", "finance & operations",
        "finance and operations",
    ],
    Vendor.SAP: [
        "sap s/4", "sap s4", "sap erp", "sap hana", "sap successfactors",
        "sap ariba", "sap concur", "sap fiori", "sap r/3", " sap ",
        "sap-løsning", "sap system",
    ],
    Vendor.SERVICENOW: [
        "servicenow", "service now", "snow platform",
    ],
    Vendor.ORACLE: [
        "oracle erp", "oracle cloud", "oracle fusion", "oracle hcm",
        "oracle financials", "oracle peoplesoft", "peoplesoft",
        "oracle e-business", "oracle ebs",
    ],
    Vendor.IFS: [
        "ifs applications", "ifs cloud", "ifs erp", " ifs ", "ifs ab",
        "industrial and financial systems",
    ],
    Vendor.SALESFORCE: [
        "salesforce", "sales cloud", "service cloud", "salesforce crm",
        "force.com", "salesforce platform",
    ],
    Vendor.WORKDAY: [
        "workday", "workday hcm", "workday finance", "workday financial",
    ],
}

# CPV codes for IT / software procurement
IT_CPV_PREFIXES = [
    "48",   # Software packages
    "72",   # IT services
    "79",   # Business services (includes some IT consulting)
]


class ProcurementNotice(BaseModel):
    notice_id: str
    title: str
    description: Optional[str] = None
    contracting_authority: Optional[str] = None
    authority_type: Optional[str] = None  # municipality, state, health, etc.
    notice_type: NoticeType = NoticeType.UNKNOWN
    published_date: Optional[date] = None
    deadline_date: Optional[date] = None
    estimated_value_nok: Optional[float] = None
    cpv_codes: list[str] = Field(default_factory=list)
    matched_vendors: list[str] = Field(default_factory=list)
    raw_url: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    def detect_vendors(self) -> list[str]:
        text = " ".join(filter(None, [self.title, self.description])).lower()
        found = []
        for vendor, keywords in VENDOR_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                found.append(vendor.value)
        return found


class VendorStats(BaseModel):
    vendor: str
    total_notices: int
    award_notices: int
    total_value_nok: float
    avg_value_nok: float
    by_year: dict[int, int]
    by_authority_type: dict[str, int]
    top_authorities: list[tuple[str, int]]
