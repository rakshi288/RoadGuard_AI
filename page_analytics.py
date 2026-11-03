"""RoadGuard AI — Accident Analytics Page"""

import streamlit as st
import plotly.express as px
import pandas as pd

CT   = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", title_font_color="#94a3b8")
SCOL = {"Damage Only":"#22c55e","Simple Injury":"#eab308","Grievous Injury":"#f97316","Fatal":"#ef4444"}
SORD = ["Damage Only","Simple Injury","Grievous Injury","Fatal"]


def show(df, stats):
    st.markdown('<div class="ptitle">📊 Accident Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="psub">Explore Karnataka accident patterns · Use filters to drill down</div>',
        unsafe_allow_html=True,
    )

    # Filters
    with st.expander("🔧 Filters", expanded=False):
        fc1,fc2,fc3 = st.columns(3)
        with fc1:
            years    = sorted(df["Year"].unique().tolist())
            sel_yr   = st.multiselect("Year", years, default=years, key="an_yr")
        with fc2:
            all_dist = sorted(df["DISTRICTNAME"].dropna().unique().tolist())
            sel_dist = st.multiselect("District (default: top 15)", all_dist,
                                      default=all_dist[:15], key="an_dist")
        with fc3:
            sel_sev  = st.multiselect("Severity", SORD, default=SORD, key="an_sev")

    filt = df.copy()
    if sel_yr:   filt = filt[filt["Year"].isin(sel_yr)]
    if sel_dist: filt = filt[filt["DISTRICTNAME"].isin(sel_dist)]
    if sel_sev:  filt = filt[filt["Severity"].astype(str).isin(sel_sev)]

    if filt.empty:
        st.warning("No data matches these filters.")
        return

    sev_str = filt["Severity"].astype(str)

    # Live metrics
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Filtered Accidents", f"{len(filt):,}")
    m2.metric("Fatal",              f"{(sev_str=='Fatal').sum():,}")
    m3.metric("Districts",          filt["DISTRICTNAME"].nunique())
    m4.metric("Years",              filt["Year"].nunique())
    st.markdown("---")

    # Row 1
    r1,r2 = st.columns([3,2])
    with r1:
        st.markdown("**📈 Year-wise Trend**")
        yr = filt.groupby(["Year", sev_str]).size().reset_index(name="Count")
        yr.columns = ["Year","Severity","Count"]
        fig = px.area(yr, x="Year", y="Count", color="Severity",
                      color_discrete_map=SCOL, category_orders={"Severity":SORD})
        fig.update_layout(**CT, height=280,
                          legend=dict(orientation="h",y=-.3),
                          margin=dict(t=5,b=40,l=0,r=0))
        fig.update_xaxes(gridcolor="#1e293b")
        fig.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)
    with r2:
        st.markdown("**🎯 Severity Split**")
        sc = sev_str.value_counts().reset_index()
        sc.columns = ["Severity","Count"]
        fig2 = px.pie(sc, names="Severity", values="Count", hole=.52,
                      color="Severity", color_discrete_map=SCOL)
        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(**CT, height=280, showlegend=False,
                           margin=dict(t=5,b=5,l=0,r=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2
    r2a,r2b = st.columns(2)
    with r2a:
        st.markdown("**🏙️ Top 15 Districts**")
        td = (filt.groupby("DISTRICTNAME").size()
               .reset_index(name="Accidents")
               .sort_values("Accidents",ascending=False).head(15))
        fig3 = px.bar(td, x="Accidents", y="DISTRICTNAME", orientation="h",
                      color="Accidents",
                      color_continuous_scale=["#1d4ed8","#3b82f6","#ef4444"])
        fig3.update_layout(**CT, height=360,
                           yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False,
                           margin=dict(t=5,b=5,l=0,r=0))
        fig3.update_xaxes(gridcolor="#1e293b")
        st.plotly_chart(fig3, use_container_width=True)

    with r2b:
        st.markdown("**🌦️ Weather Conditions**")
        wc = (filt[~filt["Weather_Clean"].isin(["Not Applicable","Others"])]
               ["Weather_Clean"].value_counts().reset_index())
        wc.columns = ["Weather","Count"]
        fig4 = px.bar(wc, x="Weather", y="Count",
                      color="Count",
                      color_continuous_scale=["#1d4ed8","#3b82f6","#60a5fa"])
        fig4.update_layout(**CT, height=360, coloraxis_showscale=False,
                           margin=dict(t=5,b=80,l=0,r=0))
        fig4.update_xaxes(tickangle=-35, gridcolor="#1e293b")
        fig4.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig4, use_container_width=True)

    # Row 3
    r3a,r3b = st.columns(2)
    with r3a:
        st.markdown("**🛣️ Road Type × Severity**")
        top_rt = filt["Road_Type"].value_counts().head(8).index
        rt_sv  = (filt[filt["Road_Type"].isin(top_rt)]
                  .groupby(["Road_Type", sev_str]).size()
                  .reset_index(name="Count"))
        rt_sv.columns = ["Road Type","Severity","Count"]
        fig5 = px.bar(rt_sv, x="Road Type", y="Count", color="Severity",
                      color_discrete_map=SCOL, barmode="stack",
                      category_orders={"Severity":SORD})
        fig5.update_layout(**CT, height=300,
                           legend=dict(orientation="h",y=-.45),
                           margin=dict(t=5,b=80,l=0,r=0))
        fig5.update_xaxes(tickangle=-35, gridcolor="#1e293b")
        fig5.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig5, use_container_width=True)

    with r3b:
        st.markdown("**🔥 District × Severity Heatmap**")
        top10 = filt["DISTRICTNAME"].value_counts().head(10).index
        hm    = (filt[filt["DISTRICTNAME"].isin(top10)]
                 .groupby(["DISTRICTNAME", sev_str]).size()
                 .reset_index(name="Count"))
        hm.columns = ["District","Severity","Count"]
        piv = (hm.pivot(index="District", columns="Severity", values="Count")
               .fillna(0).reindex(columns=[c for c in SORD if c in hm["Severity"].unique()]))
        fig6 = px.imshow(piv, color_continuous_scale="Oranges", aspect="auto")
        fig6.update_layout(**CT, height=300, margin=dict(t=5,b=5,l=0,r=0))
        st.plotly_chart(fig6, use_container_width=True)

    # Summary table
    st.markdown("---")
    st.markdown("**📋 District Summary**")
    summary = (
        filt.groupby("DISTRICTNAME").agg(
            Total=("Severity","count"),
            Fatal=("Severity",lambda x:(x.astype(str)=="Fatal").sum()),
            Grievous=("Severity",lambda x:(x.astype(str)=="Grievous Injury").sum()),
            Simple=("Severity",lambda x:(x.astype(str)=="Simple Injury").sum()),
            Damage=("Severity",lambda x:(x.astype(str)=="Damage Only").sum()),
        ).reset_index()
        .sort_values("Total",ascending=False)
        .rename(columns={"DISTRICTNAME":"District","Damage":"Damage Only"})
    )
    summary["Fatal %"] = (summary["Fatal"]/summary["Total"]*100).round(1).astype(str)+"%"
    st.dataframe(summary, use_container_width=True, height=280, hide_index=True)
