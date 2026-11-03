"""
RoadGuard AI — Dashboard
Real statistics from the Karnataka accident dataset.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

CT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
SCOL = {"Damage Only":"#22c55e","Simple Injury":"#eab308",
        "Grievous Injury":"#f97316","Fatal":"#ef4444"}
SORDER = ["Damage Only","Simple Injury","Grievous Injury","Fatal"]


def show(df, stats):
    st.markdown('<div class="page-title">📊 Karnataka Road Accident Dashboard</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">'
        'Live statistics from 2.93 lakh accident records · 2016–2023 · 38 districts'
        '</div>', unsafe_allow_html=True,
    )

    # ── KPI Row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpis = [
        (k1, "🚗", f"{stats['total_accidents']:,}",   "Total Accidents"),
        (k2, "📍", str(stats["total_districts"]),      "Districts"),
        (k3, "💀", f"{stats['fatal_count']:,}",        "Fatal Cases"),
        (k4, "🏥", f"{stats['grievous_count']:,}",     "Grievous Injuries"),
        (k5, "📅", stats["year_range"],                "Data Period"),
        (k6, "🔥", stats["most_accidents_district"].split()[0], "Busiest District"),
    ]
    for col, icon, val, label in kpis:
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{val}</div>
            <div class="kpi-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("🔧 Filter Dashboard", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            years = sorted(df["Year"].unique().tolist())
            sel_years = st.multiselect("Year", years, default=years, key="db_yr")
        with fc2:
            all_dist = sorted(df["DISTRICTNAME"].dropna().unique().tolist())
            sel_dist = st.multiselect("District", all_dist, default=all_dist[:15], key="db_dist")
        with fc3:
            sel_sev = st.multiselect("Severity", SORDER, default=SORDER, key="db_sev")

    filt = df.copy()
    if sel_years:
        filt = filt[filt["Year"].isin(sel_years)]
    if sel_dist:
        filt = filt[filt["DISTRICTNAME"].isin(sel_dist)]
    if sel_sev:
        filt = filt[filt["Severity"].astype(str).isin(sel_sev)]

    if filt.empty:
        st.warning("No data matches your filters.")
        return

    total_filt = len(filt)
    sev_str    = filt["Severity"].astype(str)

    # Live filter metrics
    fm1, fm2, fm3, fm4 = st.columns(4)
    fm1.metric("Filtered Accidents", f"{total_filt:,}")
    fm2.metric("Fatal in Filter",    f"{(sev_str=='Fatal').sum():,}")
    fm3.metric("Districts Shown",    filt["DISTRICTNAME"].nunique())
    fm4.metric("Years Shown",        filt["Year"].nunique())

    st.markdown("---")

    # ── Row 1: Trend + Donut ──────────────────────────────────────────────────
    r1, r2 = st.columns([3, 2])

    with r1:
        st.markdown("**📈 Year-wise Accident Trend by Severity**")
        yearly = (
            filt.groupby(["Year", sev_str])
            .size().reset_index(name="Accidents")
        )
        yearly.columns = ["Year","Severity","Accidents"]
        fig_trend = px.area(
            yearly, x="Year", y="Accidents", color="Severity",
            color_discrete_map=SCOL,
            category_orders={"Severity": SORDER},
        )
        fig_trend.update_layout(**CT, height=300,
                                legend=dict(orientation="h", y=-0.3),
                                margin=dict(t=10,b=40,l=0,r=0))
        fig_trend.update_xaxes(gridcolor="#1e293b")
        fig_trend.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_trend, use_container_width=True)

    with r2:
        st.markdown("**🎯 Severity Distribution**")
        sev_counts = sev_str.value_counts().reset_index()
        sev_counts.columns = ["Severity","Count"]
        fig_pie = px.pie(
            sev_counts, names="Severity", values="Count",
            hole=0.55, color="Severity", color_discrete_map=SCOL,
        )
        fig_pie.update_traces(textinfo="percent+label", textposition="outside")
        fig_pie.update_layout(**CT, height=300, showlegend=False,
                              margin=dict(t=10,b=10,l=0,r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Row 2: Districts + Weather ────────────────────────────────────────────
    r2a, r2b = st.columns(2)

    with r2a:
        st.markdown("**🏙️ Top 15 Districts by Total Accidents**")
        top_dist = (
            filt.groupby("DISTRICTNAME").size()
            .reset_index(name="Accidents")
            .sort_values("Accidents", ascending=False).head(15)
        )
        fig_dist = px.bar(
            top_dist, x="Accidents", y="DISTRICTNAME", orientation="h",
            color="Accidents",
            color_continuous_scale=["#1d4ed8","#3b82f6","#f97316","#ef4444"],
        )
        fig_dist.update_layout(**CT, height=380,
                               yaxis=dict(autorange="reversed"),
                               coloraxis_showscale=False,
                               margin=dict(t=10,b=10,l=0,r=0))
        fig_dist.update_xaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_dist, use_container_width=True)

    with r2b:
        st.markdown("**🌦️ Accidents by Weather Condition**")
        weather_c = (
            filt[~filt["Weather_Clean"].isin(["Not Applicable","Others"])]
            ["Weather_Clean"].value_counts().reset_index()
        )
        weather_c.columns = ["Weather","Accidents"]
        fig_w = px.bar(
            weather_c, x="Weather", y="Accidents",
            color="Accidents",
            color_continuous_scale=["#1d4ed8","#3b82f6","#60a5fa"],
        )
        fig_w.update_layout(**CT, height=380, coloraxis_showscale=False,
                            margin=dict(t=10,b=80,l=0,r=0))
        fig_w.update_xaxes(tickangle=-35, gridcolor="#1e293b")
        fig_w.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_w, use_container_width=True)

    # ── Row 3: Road type + Heatmap ────────────────────────────────────────────
    r3a, r3b = st.columns(2)

    with r3a:
        st.markdown("**🛣️ Road Type vs Severity**")
        top_rt = filt["Road_Type"].value_counts().head(8).index.tolist()
        rt_sev = (
            filt[filt["Road_Type"].isin(top_rt)]
            .groupby(["Road_Type", sev_str]).size()
            .reset_index(name="Count")
        )
        rt_sev.columns = ["Road Type","Severity","Count"]
        fig_rt = px.bar(
            rt_sev, x="Road Type", y="Count", color="Severity",
            color_discrete_map=SCOL, barmode="stack",
            category_orders={"Severity": SORDER},
        )
        fig_rt.update_layout(**CT, height=320, margin=dict(t=10,b=80,l=0,r=0),
                             legend=dict(orientation="h",y=-0.45))
        fig_rt.update_xaxes(tickangle=-35, gridcolor="#1e293b")
        fig_rt.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_rt, use_container_width=True)

    with r3b:
        st.markdown("**🔥 Top-10 District × Severity Heatmap**")
        top10 = filt["DISTRICTNAME"].value_counts().head(10).index.tolist()
        heat = (
            filt[filt["DISTRICTNAME"].isin(top10)]
            .groupby(["DISTRICTNAME", sev_str]).size()
            .reset_index(name="Count")
        )
        heat.columns = ["District","Severity","Count"]
        pivot = heat.pivot(index="District", columns="Severity", values="Count").fillna(0)
        # reorder columns
        pivot = pivot.reindex(columns=[c for c in SORDER if c in pivot.columns])
        fig_hm = px.imshow(pivot, color_continuous_scale="Oranges", aspect="auto")
        fig_hm.update_layout(**CT, height=320, margin=dict(t=10,b=10,l=0,r=0))
        st.plotly_chart(fig_hm, use_container_width=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📋 District Summary Table**")
    summary = (
        filt.groupby("DISTRICTNAME").agg(
            Total=("Severity","count"),
            Fatal=("Severity", lambda x: (x.astype(str)=="Fatal").sum()),
            Grievous=("Severity", lambda x: (x.astype(str)=="Grievous Injury").sum()),
            Simple=("Severity", lambda x: (x.astype(str)=="Simple Injury").sum()),
            Damage=("Severity", lambda x: (x.astype(str)=="Damage Only").sum()),
        )
        .reset_index()
        .sort_values("Total", ascending=False)
        .rename(columns={"DISTRICTNAME":"District","Damage":"Damage Only"})
    )
    summary["Fatal %"] = (summary["Fatal"] / summary["Total"] * 100).round(1).astype(str) + "%"
    st.dataframe(summary, use_container_width=True, height=280, hide_index=True)
