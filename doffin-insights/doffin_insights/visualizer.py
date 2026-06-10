"""Generate charts from analysed Doffin procurement data."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .analyzer import authority_type_breakdown, yearly_comparison
from .database import Database
from .models import VendorStats

VENDOR_COLOURS = {
    "Microsoft Dynamics": "#00A4EF",
    "SAP":                "#003366",
    "ServiceNow":         "#81B5A1",
    "Oracle":             "#C74634",
    "IFS":                "#E65C00",
    "Salesforce":         "#00A1E0",
    "Workday":            "#F5A623",
}

FONT_TITLE = {"fontsize": 14, "fontweight": "bold"}
FONT_LABEL = {"fontsize": 10}

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def _fmt_nok(x: float, _pos=None) -> str:
    if x >= 1e9:
        return f"{x/1e9:.1f}B"
    if x >= 1e6:
        return f"{x/1e6:.0f}M"
    return f"{x/1e3:.0f}k"


# ── 1. Total notice count per vendor (bar) ──────────────────────────────────

def chart_total_notices(stats: dict[str, VendorStats], out_dir: Path) -> Path:
    vendors = sorted(stats.keys(), key=lambda v: stats[v].total_notices, reverse=True)
    counts = [stats[v].total_notices for v in vendors]
    awards = [stats[v].award_notices for v in vendors]
    colours = [VENDOR_COLOURS.get(v, "#888") for v in vendors]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(vendors))
    bars = ax.bar(x, counts, color=colours, zorder=2)
    ax.bar(x, awards, color=[c + "99" for c in colours], zorder=3, label="Herav tildeling")

    ax.set_xticks(x)
    ax.set_xticklabels(vendors, rotation=20, ha="right", **FONT_LABEL)
    ax.set_ylabel("Antall kunngjøringer", **FONT_LABEL)
    ax.set_title("Totalt antall Doffin-kunngjøringer per leverandør", **FONT_TITLE)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.legend(fontsize=9)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            str(count), ha="center", va="bottom", fontsize=9,
        )

    fig.tight_layout()
    path = out_dir / "01_total_notices.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 2. Trend over years (multi-line) ─────────────────────────────────────────

def chart_yearly_trend(db: Database, out_dir: Path) -> Path:
    data = yearly_comparison(db)
    if not data:
        raise ValueError("No data for yearly trend chart")

    all_vendors = sorted(
        {v for counts in data.values() for v in counts},
        key=lambda v: sum(data[yr].get(v, 0) for yr in data),
        reverse=True,
    )
    years = sorted(data.keys())

    fig, ax = plt.subplots(figsize=(12, 6))
    for vendor in all_vendors:
        values = [data[yr].get(vendor, 0) for yr in years]
        ax.plot(
            years, values,
            marker="o", linewidth=2, markersize=5,
            label=vendor,
            color=VENDOR_COLOURS.get(vendor, None),
        )

    ax.set_xlabel("År", **FONT_LABEL)
    ax.set_ylabel("Antall kunngjøringer", **FONT_LABEL)
    ax.set_title("Etterspørsel etter ERP/CRM-systemer i offentlig sektor over tid", **FONT_TITLE)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(years)

    fig.tight_layout()
    path = out_dir / "02_yearly_trend.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 3. Authority type breakdown (stacked bar) ────────────────────────────────

def chart_authority_breakdown(db: Database, out_dir: Path) -> Path:
    data = authority_type_breakdown(db)
    if not data:
        raise ValueError("No data for authority breakdown chart")

    vendors = sorted(data.keys(), key=lambda v: sum(data[v].values()), reverse=True)
    all_auth_types = sorted(
        {at for v_data in data.values() for at in v_data},
        key=lambda at: sum(data[v].get(at, 0) for v in vendors),
        reverse=True,
    )

    df = pd.DataFrame(
        {at: [data[v].get(at, 0) for v in vendors] for at in all_auth_types},
        index=vendors,
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    df.plot(kind="bar", stacked=True, ax=ax, colormap="tab10", zorder=2)

    ax.set_xlabel("")
    ax.set_ylabel("Antall kunngjøringer", **FONT_LABEL)
    ax.set_title("Kunngjøringer per leverandør fordelt på type offentlig virksomhet", **FONT_TITLE)
    ax.set_xticklabels(vendors, rotation=20, ha="right", **FONT_LABEL)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.legend(title="Virksomhetstype", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)

    fig.tight_layout()
    path = out_dir / "03_authority_breakdown.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 4. Estimated contract value (horizontal bar) ─────────────────────────────

def chart_contract_values(stats: dict[str, VendorStats], out_dir: Path) -> Path:
    vendors = [v for v in stats if stats[v].total_value_nok > 0]
    if not vendors:
        raise ValueError("No value data available")

    vendors = sorted(vendors, key=lambda v: stats[v].total_value_nok, reverse=True)
    total_vals = [stats[v].total_value_nok for v in vendors]
    avg_vals = [stats[v].avg_value_nok for v in vendors]
    colours = [VENDOR_COLOURS.get(v, "#888") for v in vendors]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    y = np.arange(len(vendors))

    ax1.barh(y, total_vals, color=colours)
    ax1.set_yticks(y)
    ax1.set_yticklabels(vendors, **FONT_LABEL)
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_nok))
    ax1.set_title("Total estimert kontraktverdi (NOK)", **FONT_TITLE)
    ax1.grid(axis="x", alpha=0.3)

    ax2.barh(y, avg_vals, color=colours)
    ax2.set_yticks(y)
    ax2.set_yticklabels(vendors, **FONT_LABEL)
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_nok))
    ax2.set_title("Gjennomsnittlig kontraktverdi per kunngjøring (NOK)", **FONT_TITLE)
    ax2.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    path = out_dir / "04_contract_values.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 5. Market share pie ───────────────────────────────────────────────────────

def chart_market_share(stats: dict[str, VendorStats], out_dir: Path) -> Path:
    vendors = sorted(stats.keys(), key=lambda v: stats[v].total_notices, reverse=True)
    counts = [stats[v].total_notices for v in vendors]
    colours = [VENDOR_COLOURS.get(v, "#888") for v in vendors]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=vendors,
        colors=colours,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        startangle=140,
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Andel av offentlige innkjøpsannonser per leverandør", **FONT_TITLE)

    fig.tight_layout()
    path = out_dir / "05_market_share.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 6. Heatmap: vendor × authority type ──────────────────────────────────────

def chart_heatmap(db: Database, out_dir: Path) -> Path:
    data = authority_type_breakdown(db)
    if not data:
        raise ValueError("No data for heatmap")

    vendors = sorted(data.keys(), key=lambda v: sum(data[v].values()), reverse=True)
    auth_types = sorted(
        {at for v_data in data.values() for at in v_data},
        key=lambda at: sum(data[v].get(at, 0) for v in vendors),
        reverse=True,
    )

    matrix = np.array([[data[v].get(at, 0) for at in auth_types] for v in vendors], dtype=float)
    # Normalise each row so we can compare vendors of different total scale
    row_totals = matrix.sum(axis=1, keepdims=True)
    row_totals[row_totals == 0] = 1
    norm_matrix = matrix / row_totals * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(norm_matrix, aspect="auto", cmap="YlOrRd")
    plt.colorbar(im, ax=ax, label="% av leverandørens kunngjøringer")

    ax.set_xticks(range(len(auth_types)))
    ax.set_xticklabels(auth_types, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(vendors)))
    ax.set_yticklabels(vendors, fontsize=10)
    ax.set_title("Heatmap: leverandør vs. type offentlig virksomhet (%)", **FONT_TITLE)

    for i, vendor in enumerate(vendors):
        for j, at in enumerate(auth_types):
            val = norm_matrix[i, j]
            if val > 0:
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if val > 50 else "black")

    fig.tight_layout()
    path = out_dir / "06_heatmap_vendor_authority.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── 7. Top contracting authorities per vendor ─────────────────────────────────

def chart_top_authorities(stats: dict[str, VendorStats], out_dir: Path) -> Path:
    vendors = sorted(stats.keys(), key=lambda v: stats[v].total_notices, reverse=True)[:4]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Topp innkjøpere per leverandør", **FONT_TITLE)

    for ax, vendor in zip(axes.flat, vendors):
        top = stats[vendor].top_authorities[:8]
        names = [t[0][:35] for t in top]
        counts = [t[1] for t in top]
        colour = VENDOR_COLOURS.get(vendor, "#888")

        ax.barh(range(len(names)), counts, color=colour)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=8)
        ax.set_title(vendor, fontsize=11, fontweight="bold", color=colour)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.grid(axis="x", alpha=0.3)

    for ax in axes.flat[len(vendors):]:
        ax.set_visible(False)

    fig.tight_layout()
    path = out_dir / "07_top_authorities.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ── Master render function ────────────────────────────────────────────────────

def render_all(db: Database, stats: dict[str, VendorStats], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    charts = []

    renderers = [
        ("Total notices",       lambda: chart_total_notices(stats, out_dir)),
        ("Yearly trend",        lambda: chart_yearly_trend(db, out_dir)),
        ("Authority breakdown", lambda: chart_authority_breakdown(db, out_dir)),
        ("Contract values",     lambda: chart_contract_values(stats, out_dir)),
        ("Market share",        lambda: chart_market_share(stats, out_dir)),
        ("Heatmap",             lambda: chart_heatmap(db, out_dir)),
        ("Top authorities",     lambda: chart_top_authorities(stats, out_dir)),
    ]

    for name, fn in renderers:
        try:
            path = fn()
            charts.append(path)
        except ValueError as exc:
            print(f"[skip] {name}: {exc}")

    return charts
