"""
Seed the database with synthetic but realistic procurement data so you can
explore all charts immediately without needing live Doffin API access.

Run: python demo_data.py
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from doffin_insights.database import Database
from doffin_insights.models import NoticeType, ProcurementNotice

random.seed(42)

# Realistic relative demand weights observed in Nordic public procurement
VENDOR_WEIGHTS = {
    "Microsoft Dynamics": 0.31,
    "SAP":                0.22,
    "IFS":                0.14,
    "ServiceNow":         0.12,
    "Oracle":             0.09,
    "Salesforce":         0.08,
    "Workday":            0.04,
}

AUTHORITY_TYPES = {
    "Kommune":                    0.32,
    "Statsforvaltning":           0.24,
    "Helseforetak":               0.18,
    "Fylkeskommune":              0.10,
    "Universiteter og høyskoler": 0.09,
    "Forsvaret og politi":        0.04,
    "Annet statlig":              0.03,
}

AUTHORITIES = {
    "Kommune": [
        "Oslo kommune", "Bergen kommune", "Stavanger kommune", "Trondheim kommune",
        "Bærum kommune", "Asker kommune", "Kristiansand kommune", "Fredrikstad kommune",
        "Sandnes kommune", "Drammen kommune",
    ],
    "Statsforvaltning": [
        "NAV", "Skatteetaten", "Direktoratet for forvaltning og IKT (Digdir)",
        "Statens vegvesen", "Politidirektoratet", "Utdanningsdirektoratet",
        "Statsforvalteren i Oslo og Viken", "Husbanken", "Arbeidstilsynet",
    ],
    "Helseforetak": [
        "Oslo universitetssykehus HF", "Helse Sør-Øst RHF",
        "Helse Vest RHF", "St. Olavs hospital HF", "Haukeland universitetssykehus",
        "Sykehuspartner HF", "Helse Nord RHF", "Sykehuset Innlandet HF",
    ],
    "Fylkeskommune": [
        "Viken fylkeskommune", "Vestland fylkeskommune", "Trøndelag fylkeskommune",
        "Rogaland fylkeskommune", "Innlandet fylkeskommune",
    ],
    "Universiteter og høyskoler": [
        "Universitetet i Oslo", "NTNU", "Universitetet i Bergen",
        "OsloMet", "Universitetet i Stavanger",
    ],
    "Forsvaret og politi": [
        "Forsvaret", "Politidirektoratet", "Forsvarets forskningsinstitutt (FFI)",
    ],
    "Annet statlig": [
        "Norges Bank", "Statskog SF", "Enova SF",
    ],
}

# Notice type distribution: most are contract notices, some awards, few prior info
NOTICE_TYPE_WEIGHTS = [
    (NoticeType.CONTRACT, 0.55),
    (NoticeType.AWARD, 0.38),
    (NoticeType.PRIOR_INFO, 0.07),
]

# Average value in NOK per vendor (with variance)
VENDOR_AVG_VALUE = {
    "Microsoft Dynamics": 4_500_000,
    "SAP":                8_200_000,
    "IFS":                5_100_000,
    "ServiceNow":         3_800_000,
    "Oracle":             9_400_000,
    "Salesforce":         2_900_000,
    "Workday":            6_700_000,
}

# Growth trend modifier per vendor (compound annual, approximate)
VENDOR_GROWTH = {
    "Microsoft Dynamics": 0.12,
    "SAP":                0.03,
    "IFS":                0.08,
    "ServiceNow":         0.22,
    "Oracle":             -0.02,
    "Salesforce":         0.18,
    "Workday":            0.30,
}

TITLE_TEMPLATES = {
    "Microsoft Dynamics": [
        "Anskaffelse av ERP-system basert på Microsoft Dynamics 365",
        "Microsoft Dynamics 365 Business Central – implementering og drift",
        "CRM-løsning – Dynamics 365 Sales og Customer Service",
        "Modernisering av økonomi- og HR-system med D365 Finance & Operations",
        "Rammeavtale – Dynamics 365 lisenser og konsulentbistand",
    ],
    "SAP": [
        "SAP S/4HANA – innføring og migrering fra SAP ERP",
        "Rammeavtale for SAP-konsulenttjenester",
        "SAP SuccessFactors – HR-system for offentlig virksomhet",
        "Anskaffelse av SAP-lisenser og vedlikeholdsavtale",
        "SAP Ariba – innkjøpsplattform",
    ],
    "IFS": [
        "Anskaffelse av ERP-system – IFS Applications",
        "IFS Cloud – drift og forvaltning",
        "Rammeavtale IFS-konsulenttjenester",
        "Vedlikehold og videreutvikling av IFS-basert driftsystem",
    ],
    "ServiceNow": [
        "ServiceNow ITSM – IT-tjenesteadministrasjon",
        "Implementering av ServiceNow plattform",
        "ServiceNow HR Service Delivery",
        "Anskaffelse av ITSM-verktøy basert på ServiceNow",
    ],
    "Oracle": [
        "Oracle ERP Cloud – økonomi og logistikk",
        "Oracle HCM – personalsystem",
        "Rammeavtale Oracle-lisenser og support",
        "Oracle Fusion Financials – implementering",
    ],
    "Salesforce": [
        "CRM-system – Salesforce Sales Cloud",
        "Salesforce Service Cloud – kundesenter",
        "Anskaffelse av CRM-plattform (Salesforce)",
        "Salesforce implementering og konfigurasjon",
    ],
    "Workday": [
        "Workday HCM – lønn, HR og økonomi",
        "Anskaffelse av Workday Financial Management",
        "Workday – implementering og opplæring",
    ],
}


def weighted_choice(choices: dict) -> str:
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_notices(n_per_year_base: int = 18) -> list[ProcurementNotice]:
    notices = []
    notice_counter = 10000

    for year in range(2016, 2026):
        for vendor, base_weight in VENDOR_WEIGHTS.items():
            # Apply growth trend
            years_since_2016 = year - 2016
            growth = (1 + VENDOR_GROWTH[vendor]) ** years_since_2016
            expected = max(1, int(round(n_per_year_base * base_weight * growth)))

            for _ in range(expected):
                notice_counter += 1
                auth_type = weighted_choice(AUTHORITY_TYPES)
                authority = random.choice(AUTHORITIES.get(auth_type, ["Ukjent virksomhet"]))

                pub_day = date(year, random.randint(1, 12), random.randint(1, 28))

                notice_type = random.choices(
                    [nt for nt, _ in NOTICE_TYPE_WEIGHTS],
                    weights=[w for _, w in NOTICE_TYPE_WEIGHTS],
                )[0]

                avg_val = VENDOR_AVG_VALUE[vendor]
                value = max(200_000, random.gauss(avg_val, avg_val * 0.6))
                # ~30% have no value disclosed
                if random.random() < 0.30:
                    value = None

                title = random.choice(TITLE_TEMPLATES[vendor])

                notice = ProcurementNotice(
                    notice_id=f"DEMO-{notice_counter}",
                    title=title,
                    description=f"Anskaffelse knyttet til {vendor}. Virksomheten ønsker tilbud på leveranse, implementering og drift.",
                    contracting_authority=authority,
                    authority_type=auth_type,
                    notice_type=notice_type,
                    published_date=pub_day,
                    estimated_value_nok=value,
                    cpv_codes=["72000000"],
                    matched_vendors=[vendor],
                    raw_url=f"https://doffin.no/Notice/Details/DEMO-{notice_counter}",
                )
                notices.append(notice)

    return notices


def main() -> None:
    db_path = Path("doffin_insights.db")
    notices = generate_notices()
    print(f"Generated {len(notices)} synthetic notices")

    with Database(db_path) as db:
        saved = db.upsert_many(notices)
        print(f"Saved {saved} notices → {db_path}")
        print(f"Total in DB: {db.count()}, with vendor match: {db.count_with_vendor_match()}")


if __name__ == "__main__":
    main()
