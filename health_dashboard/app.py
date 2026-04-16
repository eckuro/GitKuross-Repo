"""
Norway Private Health Spending Dashboard
=========================================
Run with:  streamlit run health_dashboard/app.py

Two analytical lenses are provided:
  • Top-down  – start from national aggregates, drill into categories
  • Bottom-up – start from individual provider types, roll up to totals

Data: SSB Helseutgiftsregnskapet, OECD Health Statistics, Finans Norge
      Reference period: 2018–2022
      All monetary values in million NOK
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from health_dashboard import data as hd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Norway Private Health Spending",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Norway.svg/320px-Flag_of_Norway.svg.png",
    width=80,
)
st.sidebar.title("Controls")

selected_year = st.sidebar.selectbox(
    "Reference year",
    options=hd.YEARS,
    index=len(hd.YEARS) - 1,  # default: most recent
)

view_mode = st.sidebar.radio(
    "Analysis lens",
    options=["Both", "Top-down only", "Bottom-up only"],
    index=0,
)

show_pct = st.sidebar.checkbox("Show percentage labels", value=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Sources:** SSB Helseutgiftsregnskapet · OECD Health Statistics · Finans Norge  \n"
    "All values in **million NOK**."
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏥 Norwegian Private Health Spending Dashboard")
st.caption(
    "Private health expenditure = out-of-pocket (OOP) household payments + "
    "voluntary health insurance (VHI) claims. Public/government expenditure excluded."
)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
total_priv  = hd.PRIVATE_EXPENDITURE[selected_year]
total_oop   = hd.OOP_EXPENDITURE[selected_year]
total_vhi   = hd.VHI_EXPENDITURE[selected_year]
total_all   = hd.TOTAL_HEALTH_EXPENDITURE[selected_year]
priv_share  = total_priv / total_all * 100

prev_year = selected_year - 1 if selected_year > hd.YEARS[0] else None
delta_priv = (
    f"{(total_priv - hd.PRIVATE_EXPENDITURE[prev_year]) / hd.PRIVATE_EXPENDITURE[prev_year] * 100:+.1f}% vs {prev_year}"
    if prev_year else ""
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total private spending", f"NOK {total_priv:,.0f}M", delta_priv)
c2.metric("Out-of-pocket (OOP)",    f"NOK {total_oop:,.0f}M",
          f"{total_oop/total_priv*100:.1f}% of private")
c3.metric("Voluntary insurance",    f"NOK {total_vhi:,.0f}M",
          f"{total_vhi/total_priv*100:.1f}% of private")
c4.metric("Total national spending",f"NOK {total_all:,.0f}M")
c5.metric("Private share of total", f"{priv_share:.1f}%")

st.divider()

# ---------------------------------------------------------------------------
# Helper: humanise large numbers
# ---------------------------------------------------------------------------
def fmt_mnok(v: float) -> str:
    if v >= 1_000:
        return f"{v/1_000:.1f}B NOK"
    return f"{v:.0f}M NOK"


# ===========================================================================
# TOP-DOWN SECTION
# ===========================================================================
def render_top_down(year: int) -> None:
    st.header("📊 Top-down view")
    st.markdown(
        "Start from the **national private health total** and drill down through "
        "financing mechanisms → service categories → sub-components."
    )

    # --- Row 1: trend lines ------------------------------------------------
    with st.expander("📈 Trend: private spending 2018–2022", expanded=True):
        series = hd.get_private_totals_series()
        trend_df = pd.DataFrame(series, index=hd.YEARS).reset_index()
        trend_df = trend_df.rename(columns={"index": "Year"})
        trend_melt = trend_df.melt("Year", var_name="Category", value_name="MNOK")

        fig_trend = px.line(
            trend_melt,
            x="Year", y="MNOK", color="Category",
            markers=True,
            labels={"MNOK": "Million NOK"},
            title=f"Private health expenditure trend (MNOK)",
            color_discrete_sequence=["#2196F3", "#FF9800", "#9C27B0"],
        )
        fig_trend.update_traces(line_width=3, marker_size=8)
        fig_trend.update_layout(hovermode="x unified", legend_title_text="")
        st.plotly_chart(fig_trend, use_container_width=True)

    # --- Row 2: sunburst + waterfall ---------------------------------------
    col_sun, col_water = st.columns([1, 1])

    with col_sun:
        st.subheader("Hierarchy: Private → Mechanism → Service")
        sb_data = hd.build_sunburst_data(year)
        sb_df = pd.DataFrame(sb_data)
        fig_sun = go.Figure(go.Sunburst(
            ids=sb_df["id"],
            labels=sb_df["label"],
            parents=sb_df["parent"],
            values=sb_df["value"],
            branchvalues="total",
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} MNOK<extra></extra>",
            maxdepth=3,
        ))
        fig_sun.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=480)
        st.plotly_chart(fig_sun, use_container_width=True)
        st.caption("Click a segment to zoom in; click the centre ring to zoom out.")

    with col_water:
        st.subheader("OOP decomposition by service")
        oop_svc = hd.get_oop_by_service_for_year(year)
        oop_df  = pd.DataFrame(
            [{"Service": k, "MNOK": v} for k, v in oop_svc.items()]
        ).sort_values("MNOK", ascending=True)

        fig_h = px.bar(
            oop_df,
            x="MNOK", y="Service",
            orientation="h",
            color="Service",
            color_discrete_map=hd.SERVICE_COLOURS,
            text="MNOK" if show_pct else None,
            labels={"MNOK": "Million NOK"},
            title=f"Out-of-pocket spending by service ({year})",
        )
        if show_pct:
            total_oop_svc = oop_df["MNOK"].sum()
            fig_h.update_traces(
                texttemplate="%{x:,.0f}M (%{customdata[0]:.1f}%)",
                customdata=[[v / total_oop_svc * 100] for v in oop_df["MNOK"]],
                textposition="outside",
            )
        fig_h.update_layout(showlegend=False, height=480,
                             xaxis_title="Million NOK", yaxis_title="")
        st.plotly_chart(fig_h, use_container_width=True)

    # --- Row 3: OOP vs VHI per service ------------------------------------
    st.subheader("OOP vs VHI by service bucket")
    oop_svc = hd.get_oop_by_service_for_year(year)
    vhi_svc = hd.get_vhi_by_service_for_year(year)

    stack_data = []
    for svc in hd.SERVICE_ORDER:
        stack_data.append({"Service": svc, "Financing": "OOP",  "MNOK": oop_svc.get(svc, 0)})
        stack_data.append({"Service": svc, "Financing": "VHI",  "MNOK": vhi_svc.get(svc, 0)})
    stack_df = pd.DataFrame(stack_data)

    # Sort by combined total descending
    order = (
        stack_df.groupby("Service")["MNOK"].sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig_stack = px.bar(
        stack_df,
        x="Service", y="MNOK",
        color="Financing",
        barmode="stack",
        color_discrete_map={"OOP": "#4C72B0", "VHI": "#DD8452"},
        category_orders={"Service": order},
        labels={"MNOK": "Million NOK"},
        title=f"Private spending by service and financing mechanism ({year})",
    )
    fig_stack.update_layout(xaxis_tickangle=-35, legend_title_text="Financing")
    st.plotly_chart(fig_stack, use_container_width=True)

    # --- Row 4: OOP % share donut -----------------------------------------
    col_donut, col_vhi = st.columns(2)

    with col_donut:
        st.subheader("OOP share by service")
        oop_svc = hd.get_oop_by_service_for_year(year)
        pie_df  = pd.DataFrame(
            [{"Service": k, "MNOK": v} for k, v in oop_svc.items()]
        )
        fig_pie = px.pie(
            pie_df, values="MNOK", names="Service",
            hole=0.45,
            color="Service",
            color_discrete_map=hd.SERVICE_COLOURS,
            title=f"OOP spending share by service ({year})",
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_vhi:
        st.subheader("VHI claims by service")
        vhi_rows = [
            {"Service": svc, "MNOK": series.get(year, 0)}
            for svc, series in hd.VHI_BY_SERVICE.items()
        ]
        vhi_df = pd.DataFrame(vhi_rows).sort_values("MNOK", ascending=False)
        fig_vhi = px.bar(
            vhi_df,
            x="Service", y="MNOK",
            color="Service",
            labels={"MNOK": "Million NOK"},
            title=f"VHI claims by service ({year})",
        )
        fig_vhi.update_layout(showlegend=False, xaxis_tickangle=-35)
        st.plotly_chart(fig_vhi, use_container_width=True)

    # --- Row 5: year-on-year OOP by service heat map ----------------------
    st.subheader("Year-on-year OOP growth by service (%)")
    yoy_rows = []
    svcs = list(hd.OOP_BY_SERVICE.keys())
    for i in range(1, len(hd.YEARS)):
        yr = hd.YEARS[i]
        prev = hd.YEARS[i - 1]
        for svc in svcs:
            val   = hd.OOP_BY_SERVICE[svc][yr]
            prev_v = hd.OOP_BY_SERVICE[svc][prev]
            yoy_rows.append({
                "Service": svc,
                "Year": str(yr),
                "YoY %": round((val - prev_v) / prev_v * 100, 1),
            })
    yoy_df = pd.DataFrame(yoy_rows)
    heat_pivot = yoy_df.pivot(index="Service", columns="Year", values="YoY %")

    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".1f",
        aspect="auto",
        title="OOP YoY growth (%) by service",
        labels={"color": "YoY %"},
    )
    fig_heat.update_layout(height=400)
    st.plotly_chart(fig_heat, use_container_width=True)


# ===========================================================================
# BOTTOM-UP SECTION
# ===========================================================================
def render_bottom_up(year: int) -> None:  # noqa: ARG001 (year not used — 2022 only)
    st.header("🔢 Bottom-up view")
    st.markdown(
        "Start from **individual provider types**, then aggregate upward to "
        "service buckets and finally to the overall private total. "
        "Provider-level data is available for **2022**."
    )

    rows    = hd.build_bottom_up_table()
    prov_df = pd.DataFrame(rows)

    # --- Waterfall: providers → buckets → total ---------------------------
    st.subheader("Build-up: providers → service buckets → total private spending")

    bucket_totals = (
        prov_df.groupby("Service bucket")["Total private (MNOK)"]
        .sum()
        .reindex(hd.SERVICE_ORDER)
        .dropna()
    )
    grand_total = bucket_totals.sum()

    wf_x: list[str] = []
    wf_y: list[float] = []
    wf_measure: list[str] = []
    wf_text: list[str] = []
    wf_colour: list[str] = []

    for svc in bucket_totals.index:
        v = bucket_totals[svc]
        wf_x.append(svc)
        wf_y.append(v)
        wf_measure.append("relative")
        wf_text.append(fmt_mnok(v))
        wf_colour.append(hd.SERVICE_COLOURS.get(svc, "#888888"))

    wf_x.append("Total private")
    wf_y.append(grand_total)
    wf_measure.append("total")
    wf_text.append(fmt_mnok(grand_total))
    wf_colour.append("#1A237E")

    fig_wf = go.Figure(go.Waterfall(
        name="Build-up",
        orientation="v",
        measure=wf_measure,
        x=wf_x,
        y=wf_y,
        text=wf_text,
        textposition="outside",
        connector={"line": {"color": "rgba(0,0,0,0.3)"}},
        increasing={"marker": {"color": "#4CAF50"}},
        totals={"marker": {"color": "#1A237E"}},
        hovertemplate="%{x}<br>%{y:,.0f} MNOK<extra></extra>",
    ))
    fig_wf.update_layout(
        title="Bottom-up accumulation to total private spending (2022, MNOK)",
        waterfallgap=0.3,
        height=520,
        xaxis_tickangle=-35,
        yaxis_title="Million NOK",
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # --- Treemap: provider → bucket → total -------------------------------
    st.subheader("Treemap: provider → service bucket")
    prov_df_plot = prov_df.copy()
    prov_df_plot["Root"] = "Private spending"
    fig_tree = px.treemap(
        prov_df_plot,
        path=["Root", "Service bucket", "Provider"],
        values="Total private (MNOK)",
        color="Service bucket",
        color_discrete_map=hd.SERVICE_COLOURS,
        title="Provider-level treemap (2022) — size = total private spend",
        hover_data={"OOP (MNOK)": True, "VHI claims (MNOK)": True},
    )
    fig_tree.update_traces(textinfo="label+value")
    fig_tree.update_layout(height=600)
    st.plotly_chart(fig_tree, use_container_width=True)

    # --- OOP vs VHI split at provider level --------------------------------
    st.subheader("OOP vs VHI split at provider level (2022)")
    fig_prov = px.bar(
        prov_df.sort_values("Total private (MNOK)", ascending=True),
        x=["OOP (MNOK)", "VHI claims (MNOK)"],
        y="Provider",
        orientation="h",
        barmode="stack",
        color_discrete_map={"OOP (MNOK)": "#4C72B0", "VHI claims (MNOK)": "#DD8452"},
        labels={"value": "Million NOK", "variable": "Financing"},
        title="OOP vs VHI by provider (2022)",
        height=720,
    )
    fig_prov.update_layout(legend_title_text="Financing", yaxis_title="")
    st.plotly_chart(fig_prov, use_container_width=True)

    # --- Service bucket roll-up table -------------------------------------
    st.subheader("Service-bucket roll-up table (2022)")
    rollup = (
        prov_df.groupby("Service bucket")[
            ["OOP (MNOK)", "VHI claims (MNOK)", "Total private (MNOK)"]
        ]
        .sum()
        .reindex(hd.SERVICE_ORDER)
        .dropna()
        .reset_index()
    )
    rollup["OOP share"] = (rollup["OOP (MNOK)"] / rollup["Total private (MNOK)"] * 100).map("{:.1f}%".format)
    rollup["VHI share"] = (rollup["VHI claims (MNOK)"] / rollup["Total private (MNOK)"] * 100).map("{:.1f}%".format)

    # Totals row
    totals_row = pd.DataFrame([{
        "Service bucket": "**TOTAL**",
        "OOP (MNOK)": rollup["OOP (MNOK)"].sum(),
        "VHI claims (MNOK)": rollup["VHI claims (MNOK)"].sum(),
        "Total private (MNOK)": rollup["Total private (MNOK)"].sum(),
        "OOP share": f"{rollup['OOP (MNOK)'].sum() / rollup['Total private (MNOK)'].sum() * 100:.1f}%",
        "VHI share": f"{rollup['VHI claims (MNOK)'].sum() / rollup['Total private (MNOK)'].sum() * 100:.1f}%",
    }])
    display_df = pd.concat([rollup, totals_row], ignore_index=True)
    st.dataframe(
        display_df.style.format({
            "OOP (MNOK)": "{:,.0f}",
            "VHI claims (MNOK)": "{:,.0f}",
            "Total private (MNOK)": "{:,.0f}",
        }).background_gradient(subset=["Total private (MNOK)"], cmap="Blues"),
        use_container_width=True,
    )

    # --- Provider detail table (expandable) --------------------------------
    with st.expander("📋 Full provider-level detail"):
        st.dataframe(
            prov_df.sort_values(
                ["Service bucket", "Total private (MNOK)"], ascending=[True, False]
            ).reset_index(drop=True).style.format({
                "OOP (MNOK)": "{:,.0f}",
                "VHI claims (MNOK)": "{:,.0f}",
                "Total private (MNOK)": "{:,.0f}",
            }).background_gradient(subset=["Total private (MNOK)"], cmap="Blues"),
            use_container_width=True,
        )


# ===========================================================================
# Comparison tab (both lenses side-by-side summary)
# ===========================================================================
def render_comparison(year: int) -> None:
    st.header("🔄 Top-down vs Bottom-up reconciliation")
    st.markdown(
        "The two lenses should converge to the **same service-bucket totals**.  \n"
        "Top-down uses SSB macro aggregates; bottom-up sums provider-level estimates.  \n"
        "Small discrepancies reflect rounding and data source differences."
    )

    oop_td  = hd.get_oop_by_service_for_year(year)
    vhi_td  = hd.get_vhi_by_service_for_year(year)
    rows_bu = hd.build_bottom_up_table()
    bu_df   = pd.DataFrame(rows_bu)
    bu_by_svc = bu_df.groupby("Service bucket")["Total private (MNOK)"].sum()

    recon_rows = []
    for svc in hd.SERVICE_ORDER:
        td_total = oop_td.get(svc, 0) + vhi_td.get(svc, 0)
        bu_total = bu_by_svc.get(svc, 0)
        diff     = bu_total - td_total
        recon_rows.append({
            "Service": svc,
            "Top-down (MNOK)": td_total,
            "Bottom-up (MNOK)": bu_total,
            "Difference": diff,
            "Diff %": round(diff / td_total * 100, 1) if td_total else 0,
        })

    recon_df = pd.DataFrame(recon_rows)

    # Grouped bar chart
    melt_recon = recon_df.melt(
        id_vars="Service",
        value_vars=["Top-down (MNOK)", "Bottom-up (MNOK)"],
        var_name="Method",
        value_name="MNOK",
    )
    fig_recon = px.bar(
        melt_recon,
        x="Service", y="MNOK",
        color="Method",
        barmode="group",
        color_discrete_map={"Top-down (MNOK)": "#1565C0", "Bottom-up (MNOK)": "#EF6C00"},
        labels={"MNOK": "Million NOK"},
        title=f"Top-down vs Bottom-up by service bucket ({year}, MNOK)",
    )
    fig_recon.update_layout(xaxis_tickangle=-35, legend_title_text="Method")
    st.plotly_chart(fig_recon, use_container_width=True)

    # Reconciliation table
    st.subheader("Reconciliation table")
    styled = (
        recon_df.style
        .format({
            "Top-down (MNOK)": "{:,.0f}",
            "Bottom-up (MNOK)": "{:,.0f}",
            "Difference": "{:+,.0f}",
            "Diff %": "{:+.1f}%",
        })
        .background_gradient(subset=["Top-down (MNOK)", "Bottom-up (MNOK)"], cmap="Blues")
        .applymap(
            lambda v: "color: red" if isinstance(v, float) and abs(v) > 5 else "",
            subset=["Diff %"],
        )
    )
    st.dataframe(styled, use_container_width=True)
    st.caption(
        "Differences within ±5% are expected given provider-level estimates "
        "are built from a mix of SSB, Finans Norge, and industry reports."
    )


# ===========================================================================
# Main layout
# ===========================================================================
if view_mode == "Both":
    tab_td, tab_bu, tab_cmp = st.tabs(
        ["📊 Top-down", "🔢 Bottom-up", "🔄 Reconciliation"]
    )
    with tab_td:
        render_top_down(selected_year)
    with tab_bu:
        render_bottom_up(selected_year)
    with tab_cmp:
        render_comparison(selected_year)
elif view_mode == "Top-down only":
    render_top_down(selected_year)
else:
    render_bottom_up(selected_year)
