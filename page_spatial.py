"""RoadGuard AI — Spatial Analysis Page"""
import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
from data_loader import load_data, get_map_data

CT   = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8")
SCOL = {"Damage Only":"#22c55e","Simple Injury":"#eab308","Grievous Injury":"#f97316","Fatal":"#ef4444"}
FCOL = {"Fatal":"red","Grievous Injury":"orange","Simple Injury":"beige","Damage Only":"green"}
SORD = ["Damage Only","Simple Injury","Grievous Injury","Fatal"]
KA   = [15.3, 75.7]


@st.cache_data(show_spinner=False)
def _profile(district):
    df  = load_data()
    sub = df[df["DISTRICTNAME"] == district]
    if sub.empty: return None
    sev = sub["Severity"].astype(str)
    return {
        "total":     len(sub),
        "fatal":     int((sev=="Fatal").sum()),
        "fatal_pct": (sev=="Fatal").mean()*100,
        "grievous":  int((sev=="Grievous Injury").sum()),
        "griev_pct": (sev=="Grievous Injury").mean()*100,
        "simple":    int((sev=="Simple Injury").sum()),
        "damage":    int((sev=="Damage Only").sum()),
        "top_road":  sub["Road_Type"].value_counts().idxmax(),
        "top_weather":sub["Weather_Clean"].value_counts().idxmax(),
        "top_cause": sub["Main_Cause"].value_counts().idxmax(),
        "top_spot":  sub["Accident_Spot"].value_counts().idxmax(),
        "peak_year": int(sub["Year"].value_counts().idxmax()),
        "gps_count": int(sub["HasCoords"].sum()),
        "yr_fatal":  sub[sev=="Fatal"].groupby("Year").size().reset_index(name="Fatal"),
    }


@st.cache_data(show_spinner=False)
def _hotspots():
    df = load_data()
    g  = df.groupby("DISTRICTNAME").agg(
           Total=("Severity","count"),
           Fatal=("Severity",lambda x:(x.astype(str)=="Fatal").sum()),
           Grievous=("Severity",lambda x:(x.astype(str)=="Grievous Injury").sum()),
         ).reset_index()
    g["HighSev"] = g["Fatal"]+g["Grievous"]
    g["HighPct"] = (g["HighSev"]/g["Total"]*100).round(1)
    g["Score"]   = ((g["Fatal"]*2+g["Grievous"])/g["Total"]*100).round(2)
    return g.sort_values("Score", ascending=False)


@st.cache_data(show_spinner=False)
def _pts(district, severities, years, max_pts):
    df = get_map_data()
    if district and district != "All Districts":
        df = df[df["DISTRICTNAME"] == district]
    if severities:
        df = df[df["Severity"].astype(str).isin(severities)]
    if years:
        df = df[df["Year"].isin(years)]
    if len(df) > max_pts:
        df = df.sample(max_pts, random_state=42)
    return df.reset_index(drop=True)


def _build_map(df_pts, mode, center=None):
    c = center or (
        [df_pts["Latitude"].mean(), df_pts["Longitude"].mean()]
        if not df_pts.empty else KA
    )
    # Use OpenStreetMap — no API key required, works offline-capable
    m = folium.Map(location=c, zoom_start=9 if center else 7,
                   tiles="OpenStreetMap", prefer_canvas=True)
    if df_pts.empty: return m

    if mode == "🌡️ Heatmap":
        HeatMap(df_pts[["Latitude","Longitude"]].values.tolist(),
                radius=13, blur=18, min_opacity=.35,
                gradient={"0.3":"#3b82f6","0.6":"#22c55e","0.8":"#f97316","1":"#ef4444"}
               ).add_to(m)

    elif mode == "📍 Clustered Markers":
        cl = MarkerCluster(options={"maxClusterRadius":60,"disableClusteringAtZoom":14}).add_to(m)
        for _,r in df_pts.iterrows():
            sev = str(r["Severity"])
            folium.CircleMarker(
                [r["Latitude"],r["Longitude"]], radius=6,
                color=FCOL.get(sev,"blue"), fill=True,
                fill_color=FCOL.get(sev,"blue"), fill_opacity=.78,
                popup=folium.Popup(
                    f"<div style='font-family:sans-serif;font-size:12px;min-width:180px;'>"
                    f"<b style='color:#ef4444'>{sev}</b><br>"
                    f"<b>District:</b> {r.get('DISTRICTNAME','')}<br>"
                    f"<b>Road:</b> {r.get('Road_Type','')}<br>"
                    f"<b>Weather:</b> {r.get('Weather','')}<br>"
                    f"<b>Year:</b> {r.get('Year','')}<br>"
                    f"<b>Cause:</b> {r.get('Main_Cause','')}</div>",
                    max_width=240),
                tooltip=f"{sev} · {r.get('DISTRICTNAME','')} · {r.get('Year','')}",
            ).add_to(cl)

    elif mode == "🎯 Severity Dots":
        for _,r in df_pts.iterrows():
            sev = str(r["Severity"])
            folium.CircleMarker(
                [r["Latitude"],r["Longitude"]], radius=5,
                color=FCOL.get(sev,"blue"), fill=True,
                fill_color=FCOL.get(sev,"blue"), fill_opacity=.72,
                popup=folium.Popup(
                    f"<b>{sev}</b><br>{r.get('DISTRICTNAME','')}<br>Year: {r.get('Year','')}",
                    max_width=180),
                tooltip=sev,
            ).add_to(m)

    m.get_root().html.add_child(folium.Element("""
    <div style="position:fixed;bottom:22px;left:22px;z-index:9999;
                background:rgba(6,9,26,.93);border:1px solid #1e2d5a;
                border-radius:10px;padding:10px 14px;font-family:sans-serif;">
      <b style="color:#e2e8f0;font-size:12px;display:block;margin-bottom:4px;">Severity</b>
      <span style="color:#ef4444;font-size:13px;">●</span>
      <span style="color:#e2e8f0;font-size:11px;"> Fatal</span><br>
      <span style="color:#f97316;font-size:13px;">●</span>
      <span style="color:#e2e8f0;font-size:11px;"> Grievous</span><br>
      <span style="color:#eab308;font-size:13px;">●</span>
      <span style="color:#e2e8f0;font-size:11px;"> Simple</span><br>
      <span style="color:#22c55e;font-size:13px;">●</span>
      <span style="color:#e2e8f0;font-size:11px;"> Damage</span>
    </div>"""))
    return m


def show(df):
    st.markdown('<div class="ptitle">🗺️ Spatial Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="psub">Interactive accident map · District analyser · Hotspot ranking</div>',
        unsafe_allow_html=True,
    )

    tab_map, tab_district, tab_hotspot = st.tabs([
        "🗺️  Accident Map",
        "🔍  District Analyser",
        "🔥  Hotspot Ranking",
    ])

    # ── Tab: Accident Map ─────────────────────────────────────────────────────
    with tab_map:
        st.markdown('<div class="sh">Filter accidents and explore Karnataka</div>',
                    unsafe_allow_html=True)

        mc1,mc2,mc3,mc4,mc5 = st.columns([2,2,2,1,1])
        all_d = ["All Districts"] + sorted(df["DISTRICTNAME"].dropna().unique().tolist())
        with mc1: m_dist = st.selectbox("📍 District",  all_d, key="m_dist")
        with mc2: m_sev  = st.multiselect("🎯 Severity",
                    ["Fatal","Grievous Injury","Simple Injury","Damage Only"],
                    default=["Fatal","Grievous Injury"], key="m_sev")
        with mc3: m_yr   = st.multiselect("📅 Year",
                    sorted(df["Year"].unique().tolist()),
                    default=[], placeholder="All years", key="m_yr")
        with mc4: m_mode = st.selectbox("Mode",
                    ["🌡️ Heatmap","📍 Clustered Markers","🎯 Severity Dots"], key="m_mode")
        with mc5: m_max  = st.selectbox("Max pts",[500,1000,2000,5000],index=1,key="m_max")

        load_col,_ = st.columns([1,4])
        with load_col:
            if st.button("🗺️ Load / Refresh Map", use_container_width=True, key="m_load"):
                with st.spinner("Building map…"):
                    d  = None if m_dist=="All Districts" else m_dist
                    pt = _pts(d, m_sev or None, m_yr or None, m_max)
                    st.session_state["map_pts"]  = pt
                    st.session_state["map_mode"] = m_mode

        pts  = st.session_state.get("map_pts", pd.DataFrame())
        mode = st.session_state.get("map_mode","🌡️ Heatmap")

        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Points on Map",  f"{len(pts):,}")
        s2.metric("Districts",       pts["DISTRICTNAME"].nunique() if not pts.empty else 0)
        s3.metric("Fatal shown",     int((pts["Severity"].astype(str)=="Fatal").sum()) if not pts.empty else 0)
        s4.metric("Grievous shown",  int((pts["Severity"].astype(str)=="Grievous Injury").sum()) if not pts.empty else 0)

        fmap = _build_map(pts, mode) if not pts.empty else _build_map(pd.DataFrame(),"🌡️ Heatmap")
        st_folium(fmap, width=None, height=540, returned_objects=[])

        if pts.empty:
            st.info("Select filters above and click **Load / Refresh Map** to display accidents.")

        if not pts.empty:
            with st.expander("📋 Accident Records Table", expanded=False):
                cols = ["DISTRICTNAME","Severity","Year","Road_Type","Weather","Main_Cause","Latitude","Longitude"]
                st.dataframe(pts[cols].rename(columns={"DISTRICTNAME":"District"}),
                             use_container_width=True, height=260, hide_index=True)

    # ── Tab: District Analyser ────────────────────────────────────────────────
    with tab_district:
        all_dist = sorted(df["DISTRICTNAME"].dropna().unique().tolist())
        dc1,dc2  = st.columns([3,1])
        with dc1: sel = st.selectbox("Select district", all_dist, key="sp_sel")
        with dc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Analyse", use_container_width=True, key="sp_go"):
                st.session_state["sp_district"] = sel

        district = st.session_state.get("sp_district", all_dist[0])
        prof     = _profile(district)
        if not prof:
            st.warning("No data for this district."); return

        st.markdown(f'<div class="sh">📍 {district}</div>', unsafe_allow_html=True)

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.metric("Total",     f"{prof['total']:,}")
        k2.metric("Fatal",     f"{prof['fatal']:,}")
        k3.metric("Fatal %",   f"{prof['fatal_pct']:.1f}%")
        k4.metric("Grievous",  f"{prof['grievous']:,}")
        k5.metric("Peak Year", str(prof["peak_year"]))
        k6.metric("GPS Recs",  f"{prof['gps_count']:,}")

        st.markdown(f"""
        <div class="ib">
            Top road: <b style="color:#e2e8f0">{prof['top_road']}</b> &nbsp;·&nbsp;
            Top weather: <b style="color:#e2e8f0">{prof['top_weather']}</b> &nbsp;·&nbsp;
            Top cause: <b style="color:#e2e8f0">{prof['top_cause']}</b> &nbsp;·&nbsp;
            Top spot: <b style="color:#e2e8f0">{prof['top_spot']}</b>
        </div>""", unsafe_allow_html=True)

        # Map + trend
        dm1,dm2 = st.columns([3,2])
        with dm1:
            st.markdown("**🗺️ Accident Hotspot Map**")
            with st.spinner("Loading map…"):
                dpts   = _pts(district, None, None, 3000)
                center = ([dpts["Latitude"].mean(), dpts["Longitude"].mean()]
                          if not dpts.empty else KA)
                dmap   = _build_map(dpts, "🌡️ Heatmap", center)
                # Add fatal circles
                for _,r in dpts[dpts["Severity"].astype(str)=="Fatal"].head(200).iterrows():
                    folium.CircleMarker(
                        [r["Latitude"],r["Longitude"]], radius=5,
                        color="red", fill=True, fill_color="red", fill_opacity=.9,
                        popup=folium.Popup(
                            f"<b>FATAL</b><br>{r.get('Road_Type','')}<br>"
                            f"{r.get('Weather','')}<br>Year {r.get('Year','')}",
                            max_width=200),
                        tooltip="Fatal",
                    ).add_to(dmap)
            if not dpts.empty:
                st_folium(dmap, width=None, height=380, returned_objects=[])
            else:
                st.info("No GPS data for this district.")

        with dm2:
            st.markdown("**📈 Year-wise Trend**")
            yr = (df[df["DISTRICTNAME"]==district]
                  .groupby(["Year", df[df["DISTRICTNAME"]==district]["Severity"].astype(str)])
                  .size().reset_index(name="Count"))
            yr.columns = ["Year","Severity","Count"]
            fig_yr = px.area(yr, x="Year", y="Count", color="Severity",
                             color_discrete_map=SCOL, category_orders={"Severity":SORD})
            fig_yr.update_layout(**CT, height=175,
                                 legend=dict(orientation="h",y=-.5),
                                 margin=dict(t=5,b=50,l=0,r=0))
            fig_yr.update_xaxes(gridcolor="#0d1230")
            fig_yr.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig_yr, use_container_width=True)

            sev_d = pd.DataFrame({
                "Severity": SORD,
                "Count": [prof["damage"],prof["simple"],prof["grievous"],prof["fatal"]],
            })
            fig_d = px.pie(sev_d, names="Severity", values="Count",
                           hole=.55, color="Severity", color_discrete_map=SCOL)
            fig_d.update_traces(textinfo="percent+label", textfont_size=10)
            fig_d.update_layout(**CT, height=165, showlegend=False,
                                margin=dict(t=5,b=5,l=0,r=0))
            st.plotly_chart(fig_d, use_container_width=True)

        # Weather + road char
        sub = df[df["DISTRICTNAME"]==district]
        wc1,wc2 = st.columns(2)
        with wc1:
            st.markdown("**🌦️ Weather × Severity**")
            wd_sub = sub[~sub["Weather_Clean"].isin(["Not Applicable","Others"])]
            wd = (wd_sub.groupby(["Weather_Clean", wd_sub["Severity"].astype(str)])
                  .size().reset_index(name="Count"))
            wd.columns = ["Weather","Severity","Count"]
            fig_w = px.bar(wd, x="Weather", y="Count", color="Severity",
                           color_discrete_map=SCOL, barmode="stack",
                           category_orders={"Severity":SORD})
            fig_w.update_layout(**CT, height=280,
                                legend=dict(orientation="h",y=-.5),
                                margin=dict(t=5,b=80,l=0,r=0))
            fig_w.update_xaxes(tickangle=-35, gridcolor="#0d1230")
            fig_w.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig_w, use_container_width=True)

        with wc2:
            st.markdown("**🛣️ Road Character × Severity**")
            rd_sub = sub[~sub["Road_Character"].isin(["Not Applicable","Others"])]
            rd = (rd_sub.groupby(["Road_Character", rd_sub["Severity"].astype(str)])
                  .size().reset_index(name="Count"))
            rd.columns = ["Road Character","Severity","Count"]
            fig_r = px.bar(rd, x="Road Character", y="Count", color="Severity",
                           color_discrete_map=SCOL, barmode="stack",
                           category_orders={"Severity":SORD})
            fig_r.update_layout(**CT, height=280,
                                legend=dict(orientation="h",y=-.55),
                                margin=dict(t=5,b=100,l=0,r=0))
            fig_r.update_xaxes(tickangle=-35, gridcolor="#0d1230")
            fig_r.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig_r, use_container_width=True)

    # ── Tab: Hotspot Ranking ──────────────────────────────────────────────────
    with tab_hotspot:
        st.markdown('<div class="sh">🔥 Karnataka Hotspot Ranking</div>', unsafe_allow_html=True)
        st.caption("Hotspot Score = (Fatal×2 + Grievous) / Total × 100")

        hs = _hotspots()
        h1,h2 = st.columns(2)
        with h1:
            fig_h = px.bar(hs.head(20), x="Score", y="DISTRICTNAME",
                           orientation="h", color="Score",
                           color_continuous_scale=["#f97316","#ef4444","#7f1d1d"],
                           hover_data=["Total","Fatal","Grievous","HighPct"],
                           labels={"DISTRICTNAME":"District","Score":"Hotspot Score"})
            fig_h.update_layout(**CT, height=520,
                                yaxis=dict(autorange="reversed"),
                                coloraxis_showscale=False,
                                margin=dict(t=10,b=10,l=0,r=0))
            fig_h.update_xaxes(gridcolor="#0d1230")
            st.plotly_chart(fig_h, use_container_width=True)

        with h2:
            fig_s = px.scatter(hs.head(30), x="Total", y="Fatal",
                               size="HighSev", color="Score",
                               color_continuous_scale=["#6366f1","#f97316","#ef4444"],
                               hover_name="DISTRICTNAME",
                               labels={"Total":"Total Accidents","Fatal":"Fatal"},
                               title="Total vs Fatal")
            fig_s.update_layout(**CT, height=520,
                                coloraxis_showscale=False,
                                margin=dict(t=40,b=10,l=0,r=0))
            fig_s.update_xaxes(gridcolor="#0d1230")
            fig_s.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig_s, use_container_width=True)

        st.dataframe(
            hs.rename(columns={"DISTRICTNAME":"District","HighSev":"High Severity",
                                "HighPct":"High Severity %","Score":"Hotspot Score"})
              [["District","Total","Fatal","Grievous","High Severity","High Severity %","Hotspot Score"]],
            use_container_width=True, hide_index=True, height=360,
        )
