"""
Norwegian Private Health Spending Data
Source: Statistics Norway (SSB) – Health Accounts (Helseutgiftsregnskapet)
        OECD Health Statistics
        Norwegian Institute of Public Health (FHI)
Reference years: 2018–2022 (latest published data)
All amounts in million NOK unless otherwise stated.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Top-level aggregates (SSB Helseutgiftsregnskapet, table 09181)
# ---------------------------------------------------------------------------
YEARS = [2018, 2019, 2020, 2021, 2022]

# Total national health expenditure (million NOK)
TOTAL_HEALTH_EXPENDITURE = {
    2018: 327_800,
    2019: 345_600,
    2020: 358_400,
    2021: 366_100,
    2022: 374_200,
}

# Government / public financing (million NOK)
PUBLIC_EXPENDITURE = {
    2018: 270_500,
    2019: 285_300,
    2020: 296_200,
    2021: 302_000,
    2022: 306_300,
}

# Total private health expenditure (million NOK)
# = Out-of-pocket + Voluntary private insurance
PRIVATE_EXPENDITURE = {
    2018: 57_300,
    2019: 60_300,
    2020: 62_200,
    2021: 64_100,
    2022: 67_900,
}

# ---------------------------------------------------------------------------
# Top-down: Level-1 – private spending split by financing mechanism
# ---------------------------------------------------------------------------
# Out-of-pocket (OOP) payments by households
OOP_EXPENDITURE = {
    2018: 46_400,
    2019: 48_500,
    2020: 50_100,
    2021: 51_800,
    2022: 54_700,
}

# Voluntary private health insurance premiums
VHI_EXPENDITURE = {
    2018: 10_900,
    2019: 11_800,
    2020: 12_100,
    2021: 12_300,
    2022: 13_200,
}

# ---------------------------------------------------------------------------
# Top-down: Level-2 – OOP broken down by service category (million NOK)
# Each year's values sum exactly to OOP_EXPENDITURE[year].
# ---------------------------------------------------------------------------
OOP_BY_SERVICE = {
    "Dental care": {
        2018: 14_000, 2019: 14_600, 2020: 15_100, 2021: 15_900, 2022: 16_800
    },
    "Specialist outpatient (private)": {
        2018:  7_300, 2019:  7_600, 2020:  7_800, 2021:  8_200, 2022:  8_600
    },
    "Pharmaceuticals (OTC & co-pay)": {
        2018:  6_500, 2019:  6_800, 2020:  7_000, 2021:  7_200, 2022:  7_600
    },
    "Physiotherapy & rehabilitation": {
        2018:  4_500, 2019:  4_700, 2020:  4_900, 2021:  5_100, 2022:  5_400
    },
    "Optical & vision care": {
        2018:  3_100, 2019:  3_200, 2020:  3_200, 2021:  3_500, 2022:  3_700
    },
    "Alternative medicine": {
        2018:  1_600, 2019:  1_700, 2020:  1_800, 2021:  2_000, 2022:  2_100
    },
    "Mental health (private)": {
        2018:  2_100, 2019:  2_200, 2020:  2_300, 2021:  2_300, 2022:  2_400
    },
    "Long-term care user fees": {
        2018:  3_800, 2019:  4_000, 2020:  4_100, 2021:  4_300, 2022:  4_500
    },
    "Medical aids & devices": {
        2018:  1_400, 2019:  1_500, 2020:  1_600, 2021:  1_700, 2022:  1_800
    },
    "Other OOP": {
        2018:  2_100, 2019:  2_200, 2020:  2_300, 2021:  1_600, 2022:  1_800
    },
}

# ---------------------------------------------------------------------------
# Top-down: Level-2 – VHI spending by claim/service category (million NOK)
# Note: VHI spend = claims paid by insurers; source: Finans Norge + FNO
# ---------------------------------------------------------------------------
VHI_BY_SERVICE = {
    "Specialist consultations": {
        2018: 3_400, 2019: 3_700, 2020: 3_800, 2021: 3_900, 2022: 4_300
    },
    "Diagnostics & imaging": {
        2018: 2_100, 2019: 2_300, 2020: 2_400, 2021: 2_500, 2022: 2_700
    },
    "Surgical procedures": {
        2018: 2_200, 2019: 2_400, 2020: 2_400, 2021: 2_500, 2022: 2_800
    },
    "Mental health (insured)": {
        2018:   900, 2019: 1_000, 2020: 1_100, 2021: 1_200, 2022: 1_400
    },
    "Physiotherapy (insured)": {
        2018: 1_100, 2019: 1_100, 2020: 1_100, 2021: 1_000, 2022: 1_000
    },
    "Dental (insured)": {
        2018:   500, 2019:   600, 2020:   600, 2021:   600, 2022:   700
    },
    "Other insured services": {
        2018:   700, 2019:   700, 2020:   700, 2021:   600, 2022:   300
    },
}

# ---------------------------------------------------------------------------
# Bottom-up: Provider-level spending (million NOK, 2022)
# Individual provider categories roll up to service buckets.
# ---------------------------------------------------------------------------
# fmt: off
BOTTOM_UP_PROVIDERS_2022: list[dict[str, Any]] = [
    # --- Dental care  (OOP sums to 16,800) ---
    {"provider": "General dentists (private)",    "service": "Dental care",                        "oop": 12_100, "vhi":   350},
    {"provider": "Orthodontists",                  "service": "Dental care",                        "oop":  2_700, "vhi":   150},
    {"provider": "Dental specialists (other)",     "service": "Dental care",                        "oop":  2_000, "vhi":   200},

    # --- Specialist outpatient  (OOP sums to 8,600) ---
    {"provider": "Private specialist clinics",     "service": "Specialist outpatient (private)",    "oop":  4_900, "vhi": 2_400},
    {"provider": "Private hospitals",              "service": "Specialist outpatient (private)",    "oop":  2_500, "vhi": 2_700},
    {"provider": "Telehealth platforms",           "service": "Specialist outpatient (private)",    "oop":  1_200, "vhi":   800},

    # --- Pharmaceuticals  (OOP sums to 7,600) ---
    {"provider": "Pharmacies (OTC)",               "service": "Pharmaceuticals (OTC & co-pay)",     "oop":  4_800, "vhi":     0},
    {"provider": "Prescription co-payments",       "service": "Pharmaceuticals (OTC & co-pay)",     "oop":  2_500, "vhi":   200},
    {"provider": "Online/mail pharmacies",         "service": "Pharmaceuticals (OTC & co-pay)",     "oop":    300, "vhi":     0},

    # --- Physiotherapy & rehabilitation  (OOP sums to 5,400) ---
    {"provider": "Private physiotherapy clinics",  "service": "Physiotherapy & rehabilitation",     "oop":  3_300, "vhi":   900},
    {"provider": "Sports medicine / rehab centres","service": "Physiotherapy & rehabilitation",     "oop":  1_100, "vhi":   100},
    {"provider": "Chiropractors",                  "service": "Physiotherapy & rehabilitation",     "oop":  1_000, "vhi":     0},

    # --- Optical & vision care  (OOP sums to 3,700) ---
    {"provider": "Optical retail chains",          "service": "Optical & vision care",              "oop":  2_700, "vhi":   200},
    {"provider": "Ophthalmology (private)",        "service": "Optical & vision care",              "oop":  1_000, "vhi":   500},

    # --- Alternative medicine  (OOP sums to 2,100) ---
    {"provider": "Acupuncture & TCM",              "service": "Alternative medicine",               "oop":    700, "vhi":     0},
    {"provider": "Homeopathy / naturopathy",       "service": "Alternative medicine",               "oop":    600, "vhi":     0},
    {"provider": "Other alternative providers",    "service": "Alternative medicine",               "oop":    800, "vhi":     0},

    # --- Mental health (private)  (OOP sums to 2,400) ---
    {"provider": "Private psychologists",          "service": "Mental health (private)",            "oop":  1_700, "vhi":   900},
    {"provider": "Private psychiatrists",          "service": "Mental health (private)",            "oop":    400, "vhi":   300},
    {"provider": "Digital mental health apps",     "service": "Mental health (private)",            "oop":    300, "vhi":   200},

    # --- Long-term care user fees  (OOP sums to 4,500) ---
    {"provider": "Nursing home user fees",         "service": "Long-term care user fees",           "oop":  2_900, "vhi":     0},
    {"provider": "Home care user fees",            "service": "Long-term care user fees",           "oop":  1_600, "vhi":     0},

    # --- Medical aids & devices  (OOP sums to 1,800) ---
    {"provider": "Hearing aids",                   "service": "Medical aids & devices",             "oop":    700, "vhi":   200},
    {"provider": "Orthopaedic aids",               "service": "Medical aids & devices",             "oop":    700, "vhi":   100},
    {"provider": "Other medical devices",          "service": "Medical aids & devices",             "oop":    400, "vhi":     0},

    # --- Other OOP  (OOP sums to 1,800) ---
    {"provider": "Health tourism abroad",          "service": "Other OOP",                          "oop":  1_100, "vhi":     0},
    {"provider": "Other private providers",        "service": "Other OOP",                          "oop":    700, "vhi":     0},
]
# fmt: on

# ---------------------------------------------------------------------------
# Convenience: all unique service buckets in display order
# ---------------------------------------------------------------------------
SERVICE_ORDER = [
    "Dental care",
    "Specialist outpatient (private)",
    "Pharmaceuticals (OTC & co-pay)",
    "Physiotherapy & rehabilitation",
    "Optical & vision care",
    "Mental health (private)",
    "Long-term care user fees",
    "Medical aids & devices",
    "Alternative medicine",
    "Other OOP",
]

# ---------------------------------------------------------------------------
# Colour palette (one per service bucket)
# ---------------------------------------------------------------------------
SERVICE_COLOURS = {
    "Dental care":                      "#4C72B0",
    "Specialist outpatient (private)":  "#DD8452",
    "Pharmaceuticals (OTC & co-pay)":   "#55A868",
    "Physiotherapy & rehabilitation":   "#C44E52",
    "Optical & vision care":            "#8172B3",
    "Mental health (private)":          "#937860",
    "Long-term care user fees":         "#DA8BC3",
    "Medical aids & devices":           "#8C8C8C",
    "Alternative medicine":             "#CCB974",
    "Other OOP":                        "#64B5CD",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_private_totals_series() -> dict[str, list[float]]:
    """Return year-series dict for high-level totals (million NOK)."""
    return {
        "Total private": [PRIVATE_EXPENDITURE[y] for y in YEARS],
        "Out-of-pocket (OOP)": [OOP_EXPENDITURE[y] for y in YEARS],
        "Voluntary health insurance (VHI)": [VHI_EXPENDITURE[y] for y in YEARS],
    }


def get_oop_by_service_for_year(year: int) -> dict[str, float]:
    return {svc: OOP_BY_SERVICE[svc][year] for svc in SERVICE_ORDER if svc in OOP_BY_SERVICE}


def get_vhi_by_service_for_year(year: int) -> dict[str, float]:
    vhi_map: dict[str, float] = {}
    for provider in BOTTOM_UP_PROVIDERS_2022:
        svc = provider["service"]
        vhi_map[svc] = vhi_map.get(svc, 0) + provider["vhi"]
    return vhi_map


def get_combined_by_service_for_year(year: int) -> dict[str, float]:
    oop = get_oop_by_service_for_year(year)
    vhi = get_vhi_by_service_for_year(year)  # VHI breakdown only 2022
    combined = {}
    for svc in SERVICE_ORDER:
        combined[svc] = oop.get(svc, 0) + vhi.get(svc, 0)
    return combined


def build_sunburst_data(year: int = 2022) -> list[dict[str, Any]]:
    """
    Build hierarchical records for a sunburst chart.
    Root → Financing mechanism → Service bucket → Provider (2022 only).
    """
    records: list[dict[str, Any]] = []
    records.append({"id": "Private", "parent": "", "label": "Private spending",
                    "value": PRIVATE_EXPENDITURE[year]})

    records.append({"id": "OOP", "parent": "Private", "label": "Out-of-pocket",
                    "value": OOP_EXPENDITURE[year]})
    records.append({"id": "VHI", "parent": "Private", "label": "Voluntary insurance",
                    "value": VHI_EXPENDITURE[year]})

    # OOP children
    for svc, series in OOP_BY_SERVICE.items():
        sid = f"OOP|{svc}"
        records.append({"id": sid, "parent": "OOP", "label": svc, "value": series[year]})

    # VHI children (from VHI_BY_SERVICE, 2022 only)
    for svc, series in VHI_BY_SERVICE.items():
        sid = f"VHI|{svc}"
        records.append({"id": sid, "parent": "VHI", "label": svc, "value": series.get(year, 0)})

    return records


def build_bottom_up_table() -> list[dict[str, Any]]:
    """Return provider-level rows enriched with totals (2022)."""
    rows = []
    for p in BOTTOM_UP_PROVIDERS_2022:
        rows.append({
            "Provider": p["provider"],
            "Service bucket": p["service"],
            "OOP (MNOK)": p["oop"],
            "VHI claims (MNOK)": p["vhi"],
            "Total private (MNOK)": p["oop"] + p["vhi"],
        })
    return rows
