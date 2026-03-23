"""Share of Wallet dashboard data models and sample data."""

from dataclasses import dataclass, field

TOTAL_BUSD = 5.5

# Segment definitions with sub-segments and BUSD allocations
SEGMENTS = {
    "Acquisition": {
        "total": 2.06,
        "color": "#4C78A8",
        "sub_segments": {
            "Direct Sales": 0.72,
            "Partner Channels": 0.58,
            "Digital Marketing": 0.43,
            "Customer Referrals": 0.33,
        },
    },
    "Processing": {
        "total": 1.87,
        "color": "#F58518",
        "sub_segments": {
            "Transaction Processing": 0.68,
            "Payment Processing": 0.54,
            "Data Processing": 0.41,
            "Settlement & Clearing": 0.24,
        },
    },
    "Consumption": {
        "total": 1.57,
        "color": "#54A24B",
        "sub_segments": {
            "Enterprise": 0.62,
            "SMB": 0.51,
            "Consumer": 0.28,
            "Platform & API": 0.16,
        },
    },
}

# Geographic breakdown (BUSD) — each geo row has segment-level detail
GEOGRAPHIES = {
    "North America": {
        "total": 2.20,
        "color": "#4C78A8",
        "segments": {
            "Acquisition": 0.83,
            "Processing": 0.75,
            "Consumption": 0.62,
        },
    },
    "Europe": {
        "total": 1.48,
        "color": "#F58518",
        "segments": {
            "Acquisition": 0.56,
            "Processing": 0.50,
            "Consumption": 0.42,
        },
    },
    "Asia Pacific": {
        "total": 1.21,
        "color": "#54A24B",
        "segments": {
            "Acquisition": 0.46,
            "Processing": 0.40,
            "Consumption": 0.35,
        },
    },
    "Latin America": {
        "total": 0.38,
        "color": "#E45756",
        "segments": {
            "Acquisition": 0.14,
            "Processing": 0.14,
            "Consumption": 0.10,
        },
    },
    "Middle East & Africa": {
        "total": 0.23,
        "color": "#72B7B2",
        "segments": {
            "Acquisition": 0.07,
            "Processing": 0.08,
            "Consumption": 0.08,
        },
    },
}

# ISO alpha-3 country codes for choropleth (representative countries per region)
COUNTRY_SOW = {
    # North America
    "USA": 1.75,
    "CAN": 0.30,
    "MEX": 0.15,
    # Europe
    "GBR": 0.38,
    "DEU": 0.30,
    "FRA": 0.24,
    "NLD": 0.18,
    "SWE": 0.14,
    "NOR": 0.10,
    "CHE": 0.14,
    # Asia Pacific
    "JPN": 0.32,
    "AUS": 0.22,
    "SGP": 0.18,
    "IND": 0.25,
    "KOR": 0.14,
    "HKG": 0.10,
    # Latin America
    "BRA": 0.18,
    "ARG": 0.10,
    "COL": 0.10,
    # Middle East & Africa
    "ARE": 0.10,
    "SAU": 0.08,
    "ZAF": 0.05,
}

# YoY growth rates by segment (%)
SEGMENT_GROWTH = {
    "Acquisition": 12.4,
    "Processing": 8.7,
    "Consumption": 15.2,
}

# YoY growth rates by geography (%)
GEO_GROWTH = {
    "North America": 9.5,
    "Europe": 7.2,
    "Asia Pacific": 18.6,
    "Latin America": 22.1,
    "Middle East & Africa": 31.4,
}

# Quarterly trend data (BUSD) — last 5 quarters
QUARTERLY_TREND = {
    "Q3 2024": {"Acquisition": 1.82, "Processing": 1.65, "Consumption": 1.38},
    "Q4 2024": {"Acquisition": 1.90, "Processing": 1.72, "Consumption": 1.44},
    "Q1 2025": {"Acquisition": 1.97, "Processing": 1.78, "Consumption": 1.49},
    "Q2 2025": {"Acquisition": 2.01, "Processing": 1.83, "Consumption": 1.53},
    "Q3 2025": {"Acquisition": 2.06, "Processing": 1.87, "Consumption": 1.57},
}
