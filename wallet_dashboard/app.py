"""Share of Wallet Dashboard — Acquisition, Processing & Consumption segments.

Run with:
    streamlit run wallet_dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from wallet_dashboard.data import (
    TOTAL_BUSD,
    SEGMENTS,
    GEOGRAPHIES,
    COUNTRY_SOW,
    SEGMENT_GROWTH,
    GEO_GROWTH,
    QUARTERLY_TREND,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Share of Wallet Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #1e2130;
        border-radius: 8px;
        padding: 16px 20px;
        border-left: 4px solid;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #ffffff; }
    .metric-label { font-size: 0.85rem; color: #a0a0b0; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-delta { font-size: 0.9rem; font-weight: 600; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: #e0e0f0; margin-bottom: 0.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filters")

    selected_geos = st.multiselect(
        "Geography",
        options=list(GEOGRAPHIES.keys()),
        default=list(GEOGRAPHIES.keys()),
    )

    selected_segments = st.multiselect(
        "Segment",
        options=list(SEGMENTS.keys()),
        default=list(SEGMENTS.keys()),
    )

    st.divider()
    st.caption("Data as of Q3 2025 · Live Production")

# ── Derived filtered data ──────────────────────────────────────────────────────
# If no selection default to all
if not selected_geos:
    selected_geos = list(GEOGRAPHIES.keys())
if not selected_segments:
    selected_segments = list(SEGMENTS.keys())

filtered_total = sum(
    GEOGRAPHIES[g]["segments"].get(s, 0)
    for g in selected_geos
    for s in selected_segments
)

filtered_seg_totals = {
    s: sum(GEOGRAPHIES[g]["segments"].get(s, 0) for g in selected_geos)
    for s in selected_segments
}

filtered_geo_totals = {
    g: sum(GEOGRAPHIES[g]["segments"].get(s, 0) for s in selected_segments)
    for g in selected_geos
}

# ── Title ──────────────────────────────────────────────────────────────────────
st.title("Share of Wallet Dashboard")
st.markdown(
    "**Live Production** · Segments: Acquisition / Processing / Consumption  ·  "
    f"Universe: **{TOTAL_BUSD:.1f} BUSD**"
)

st.divider()

# ── KPI row ────────────────────────────────────────────────────────────────────
kpi_cols = st.columns(5)

kpi_data = [
    ("Total SOW", filtered_total, None, "#4C78A8"),
    *[
        (
            seg,
            filtered_seg_totals[seg],
            SEGMENT_GROWTH.get(seg),
            SEGMENTS[seg]["color"],
        )
        for seg in selected_segments
    ],
]

# Pad to 5 columns
while len(kpi_data) < 5:
    kpi_data.append(None)

for col, data in zip(kpi_cols, kpi_data[:5]):
    with col:
        if data is None:
            continue
        label, value, growth, color = data
        delta_html = ""
        if growth is not None:
            arrow = "▲" if growth >= 0 else "▼"
            delta_color = "#4caf50" if growth >= 0 else "#f44336"
            delta_html = (
                f'<div class="metric-delta" style="color:{delta_color}">'
                f"{arrow} {abs(growth):.1f}% YoY</div>"
            )
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color:{color}">
                <div class="metric-label">{label}</div>
                <div class="metric-value">${value:.2f}B</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Row 1: Segment donut + Sub-segment bar ─────────────────────────────────────
col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.markdown('<div class="section-header">SOW by Segment</div>', unsafe_allow_html=True)

    fig_donut = go.Figure(
        go.Pie(
            labels=list(filtered_seg_totals.keys()),
            values=list(filtered_seg_totals.values()),
            hole=0.55,
            marker_colors=[SEGMENTS[s]["color"] for s in filtered_seg_totals],
            textinfo="label+percent",
            hovertemplate="%{label}<br>$%{value:.2f}B<br>%{percent}<extra></extra>",
        )
    )
    fig_donut.add_annotation(
        text=f"${filtered_total:.2f}B",
        x=0.5,
        y=0.5,
        font=dict(size=22, color="white", family="Arial Black"),
        showarrow=False,
    )
    fig_donut.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=300,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.markdown('<div class="section-header">Sub-segment Breakdown</div>', unsafe_allow_html=True)

    sub_records = []
    for seg in selected_segments:
        for sub, val in SEGMENTS[seg]["sub_segments"].items():
            # Scale sub-segment values proportionally to filtered geography share
            geo_scale = filtered_seg_totals[seg] / SEGMENTS[seg]["total"] if SEGMENTS[seg]["total"] else 1
            sub_records.append(
                {"Segment": seg, "Sub-segment": sub, "BUSD": round(val * geo_scale, 3)}
            )

    df_sub = pd.DataFrame(sub_records)

    fig_sub = px.bar(
        df_sub,
        x="BUSD",
        y="Sub-segment",
        color="Segment",
        orientation="h",
        color_discrete_map={s: SEGMENTS[s]["color"] for s in SEGMENTS},
        text="BUSD",
        labels={"BUSD": "BUSD"},
    )
    fig_sub.update_traces(texttemplate="$%{text:.2f}B", textposition="outside")
    fig_sub.update_layout(
        margin=dict(t=10, b=10, l=10, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#2a2d3e", title="BUSD"),
        yaxis=dict(gridcolor="#2a2d3e"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300,
    )
    st.plotly_chart(fig_sub, use_container_width=True)

# ── Row 2: Geography map + geo bar ────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Geographic Breakdown</div>', unsafe_allow_html=True)

col_map, col_geo_bar = st.columns([1.6, 1])

with col_map:
    # Build country-level df, filtering by selected geographies
    # Simple approach: scale COUNTRY_SOW proportionally to filtered_total / TOTAL_BUSD
    scale = filtered_total / TOTAL_BUSD if TOTAL_BUSD else 1
    country_df = pd.DataFrame(
        [
            {"iso_alpha": iso, "SOW (BUSD)": round(val * scale, 3)}
            for iso, val in COUNTRY_SOW.items()
        ]
    )

    fig_map = px.choropleth(
        country_df,
        locations="iso_alpha",
        color="SOW (BUSD)",
        color_continuous_scale=["#1e2130", "#4C78A8", "#00d4ff"],
        range_color=[0, country_df["SOW (BUSD)"].max()],
        labels={"SOW (BUSD)": "BUSD"},
    )
    fig_map.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#3a3d4e",
            bgcolor="rgba(0,0,0,0)",
            landcolor="#2a2d3e",
            showland=True,
            showocean=True,
            oceancolor="#1e2130",
            lakecolor="#1e2130",
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="BUSD",
            tickfont=dict(color="white"),
            titlefont=dict(color="white"),
        ),
        height=340,
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_geo_bar:
    geo_df = pd.DataFrame(
        [
            {
                "Region": g,
                "BUSD": filtered_geo_totals[g],
                "Growth": GEO_GROWTH.get(g, 0),
            }
            for g in selected_geos
        ]
    ).sort_values("BUSD", ascending=True)

    fig_geo = go.Figure()
    fig_geo.add_trace(
        go.Bar(
            x=geo_df["BUSD"],
            y=geo_df["Region"],
            orientation="h",
            marker_color=[GEOGRAPHIES[g]["color"] for g in geo_df["Region"]],
            text=[f"${v:.2f}B  {'+' if g >= 0 else ''}{g:.1f}%" for v, g in zip(geo_df["BUSD"], geo_df["Growth"])],
            textposition="outside",
            hovertemplate="%{y}<br>$%{x:.2f}B<extra></extra>",
        )
    )
    fig_geo.update_layout(
        margin=dict(t=10, b=10, l=10, r=100),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#2a2d3e", title="BUSD"),
        yaxis=dict(gridcolor="#2a2d3e"),
        height=340,
    )
    st.plotly_chart(fig_geo, use_container_width=True)

# ── Row 3: Geo × Segment heatmap ──────────────────────────────────────────────
st.divider()
st.markdown(
    '<div class="section-header">Geography × Segment Matrix (BUSD)</div>',
    unsafe_allow_html=True,
)

matrix_data = []
for g in selected_geos:
    row = {"Region": g}
    for s in selected_segments:
        row[s] = GEOGRAPHIES[g]["segments"].get(s, 0)
    matrix_data.append(row)

df_matrix = pd.DataFrame(matrix_data).set_index("Region")

fig_heat = go.Figure(
    go.Heatmap(
        z=df_matrix.values,
        x=df_matrix.columns.tolist(),
        y=df_matrix.index.tolist(),
        colorscale=[[0, "#1e2130"], [0.5, "#4C78A8"], [1, "#00d4ff"]],
        text=[[f"${v:.2f}B" for v in row] for row in df_matrix.values],
        texttemplate="%{text}",
        hovertemplate="%{y} · %{x}<br>$%{z:.2f}B<extra></extra>",
        showscale=True,
        colorbar=dict(
            title="BUSD",
            tickfont=dict(color="white"),
            titlefont=dict(color="white"),
        ),
    )
)
fig_heat.update_layout(
    margin=dict(t=10, b=10, l=120, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    xaxis=dict(side="top"),
    height=250,
)
st.plotly_chart(fig_heat, use_container_width=True)

# ── Row 4: Quarterly trend ─────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Quarterly Trend (BUSD)</div>', unsafe_allow_html=True)

trend_records = []
for quarter, seg_vals in QUARTERLY_TREND.items():
    for seg, val in seg_vals.items():
        if seg in selected_segments:
            trend_records.append({"Quarter": quarter, "Segment": seg, "BUSD": val})

df_trend = pd.DataFrame(trend_records)

fig_trend = px.line(
    df_trend,
    x="Quarter",
    y="BUSD",
    color="Segment",
    markers=True,
    color_discrete_map={s: SEGMENTS[s]["color"] for s in SEGMENTS},
)
fig_trend.update_traces(line=dict(width=2.5))
fig_trend.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    xaxis=dict(gridcolor="#2a2d3e"),
    yaxis=dict(gridcolor="#2a2d3e", title="BUSD"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=260,
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Share of Wallet · Live Production Environment · "
    "Segments: Acquisition, Processing, Consumption · "
    f"Total addressable wallet: ${TOTAL_BUSD:.1f} BUSD"
)
