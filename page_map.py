"""
RoadGuard AI — Interactive Accident Map
Real GPS-validated accident locations from the Karnataka dataset.
"""

import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster, FastMarkerCluster
from streamlit_folium import st_folium
import pandas as pd
from data_loader import get_map_data, get_districts

SEVERITY_COLOR = {
    "Fatal":           "#ef4444",
    "Grievous Injury": "#f97316",
    "Simple Injury":   "#eab308",
    "Damage Only":     "#22c55e",
}
FOLIUM_COLOR = {
    "Fatal": "red", "Grievous Injury": "orange",
    "Simple Injury": "beige", "Damage Only": "green",
}
KARNATAKA_CENTER = [15.3, 75.7]


@st.cache_data(show_spinner=False)
def _load_map_subset(district_tuple, severity_tuple, years_tuple, max_pts):
    df = get_map_data()
    if district_tuple:
        df = df[df["DISTRICTNAME"].isin(district_tuple)]
    if severity_tuple:
        df = df[df["Severity"].astype(str).isin(severity_tuple)]
    if years_tuple:
        df = df[df["Year"].isin(years_tuple)]
    if len(df) > max_pts:
        df = df.sample(max_pts, random_state=42)
    return df.reset_index(drop=True)


def _build_map(df_map, mode):
    m = folium.Map(
        location=KARNATAKA_CENTER,
        zoom_start=7,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )
    if df_map.empty:
        return m

    if mode == "🌡️ Heatmap":
        pts = df_map[["Latitude", "Longitude"]].dropna().values.tolist()
        HeatMap(
            pts, radius=12, blur=18, min_opacity=0.35,
            gradient={"0.3": "#3b82f6", "0.6": "#22c55e",
                      "0.8": "#f97316", "1.0": "#ef4444"},
        ).add_to(m)

    elif mode == "📍 Clustered Markers":
        cluster = MarkerCluster(
            options={"maxClusterRadius": 60, "disableClusteringAtZoom": 13}
        ).add_to(m)
        for _, row in df_map.iterrows():
            sev  = str(row["Severity"])
            col  = FOLIUM_COLOR.get(sev, "blue")
            html = (
                f"<div style='font-family:sans-serif;font-size:12px;min-width:180px;'>"
                f"<b style='color:#1e293b'>{sev}</b><br>"
                f"District: {row.get('DISTRICTNAME','—')}<br>"
                f"Road: {row.get('Road_Type','—')}<br>"
                f"Weather: {row.get('Weather','—')}<br>"
                f"Year: {row.get('Year','—')}<br>"
                f"Cause: {row.get('Main_Cause','—')}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=6, color=col, fill=True,
                fill_color=col, fill_opacity=0.75,
                popup=folium.Popup(html, max_width=240),
                tooltip=f"{sev} — {row.get('DISTRICTNAME','')} {row.get('Year','')}",
            ).add_to(cluster)

    elif mode == "🎯 Severity Dots":
        for _, row in df_map.iterrows():
            sev = str(row["Severity"])
            col = SEVERITY_COLOR.get(sev, "#3b82f6")
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5, color=col, fill=True,
                fill_color=col, fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{sev}</b><br>{row.get('DISTRICTNAME','')}<br>"
                    f"Road: {row.get('Road_Type','')}<br>Year: {row.get('Year','')}",
                    max_width=200,
                ),
                tooltip=sev,
            ).add_to(m)

    # Legend overlay
    legend = """
    <div style="position:fixed;bottom:28px;left:28px;z-index:9999;
                background:rgba(15,23,42,0.92);border:1px solid #334155;
                border-radius:10px;padding:12px 16px;font-family:sans-serif;">
      <b style="color:#e2e8f0;font-size:13px;">Severity</b><br>
      <span style="color:#ef4444">●</span> <span style="color:#e2e8f0;font-size:12px;">Fatal</span><br>
      <span style="color:#f97316">●</span> <span style="color:#e2e8f0;font-size:12px;">Grievous Injury</span><br>
      <span style="color:#eab308">●</span> <span style="color:#e2e8f0;font-size:12px;">Simple Injury</span><br>
      <span style="color:#22c55e">●</span> <span style="color:#e2e8f0;font-size:12px;">Damage Only</span>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    return m


def show():
    st.markdown('<div class="page-title">🗺️ Interactive Karnataka Accident Map</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">'
        '95,713 GPS-validated accident locations · Filter by district, severity, and year · '
        'Click markers for full accident details'
        '</div>', unsafe_allow_html=True,
    )

    all_districts = get_districts()
    all_years     = sorted(
        get_map_data()["Year"].dropna().astype(int).unique().tolist()
    )

    # ── Filter panel ──────────────────────────────────────────────────────────
    with st.container():
        fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 1, 1])
        with fc1:
            sel_dist = st.multiselect(
                "📍 District",
                all_districts, default=[],
                placeholder="All districts", key="m_dist",
            )
        with fc2:
            sel_sev = st.multiselect(
                "🎯 Severity",
                ["Fatal", "Grievous Injury", "Simple Injury", "Damage Only"],
                default=["Fatal", "Grievous Injury"],
                key="m_sev",
            )
        with fc3:
            sel_years = st.multiselect(
                "📅 Year",
                all_years, default=[], placeholder="All years", key="m_yr",
            )
        with fc4:
            mode = st.selectbox(
                "🗺️ Mode",
                ["🌡️ Heatmap", "📍 Clustered Markers", "🎯 Severity Dots"],
                key="m_mode",
            )
        with fc5:
            max_pts = st.selectbox(
                "Max pts",
                [500, 1000, 2000, 5000],
                index=1, key="m_max",
            )

    load_col, _ = st.columns([1, 3])
    with load_col:
        load_map = st.button("🗺️ Load / Refresh Map", use_container_width=True, key="m_load")

    # Keep last map in session state so it persists across reruns
    if load_map or "map_obj" not in st.session_state:
        with st.spinner("Building map…"):
            df_map = _load_map_subset(
                tuple(sel_dist)  if sel_dist  else None,
                tuple(sel_sev)   if sel_sev   else None,
                tuple(sel_years) if sel_years else None,
                max_pts,
            )
            st.session_state["map_obj"]  = _build_map(df_map, mode)
            st.session_state["map_df"]   = df_map
            st.session_state["map_mode"] = mode

    df_map = st.session_state.get("map_df", pd.DataFrame())

    # Quick stats
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Points on Map",  f"{len(df_map):,}")
    s2.metric("Districts",       df_map["DISTRICTNAME"].nunique() if not df_map.empty else 0)
    s3.metric("Fatal",           int((df_map["Severity"].astype(str) == "Fatal").sum()) if not df_map.empty else 0)
    s4.metric("Grievous",        int((df_map["Severity"].astype(str) == "Grievous Injury").sum()) if not df_map.empty else 0)
    s5.metric("Years covered",   df_map["Year"].nunique() if not df_map.empty else 0)

    # Map
    st_folium(
        st.session_state["map_obj"],
        width=None, height=560,
        returned_objects=[],
    )

    if df_map.empty:
        st.warning("No records match these filters. Adjust selections and click **Load / Refresh Map**.")
        return

    # ── Accident details table ────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📋 View Accident Records on Map", expanded=False):
        cols_show = ["DISTRICTNAME", "Severity", "Year", "Road_Type",
                     "Weather", "Main_Cause", "Latitude", "Longitude"]
        st.dataframe(
            df_map[cols_show].rename(columns={"DISTRICTNAME": "District"}),
            use_container_width=True,
            height=300,
            hide_index=True,
        )

    # ── District breakdown ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">📊 Severity Breakdown for Mapped Points</div>',
                unsafe_allow_html=True)

    bc1, bc2 = st.columns(2)
    with bc1:
        import plotly.express as px
        CT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        dist_sev = (
            df_map.groupby(["DISTRICTNAME", df_map["Severity"].astype(str)])
            .size().reset_index(name="Count")
        )
        dist_sev.columns = ["District", "Severity", "Count"]
        dist_top = dist_sev.groupby("District")["Count"].sum().nlargest(10).index
        dist_sev = dist_sev[dist_sev["District"].isin(dist_top)]
        sev_colors = {"Fatal":"#ef4444","Grievous Injury":"#f97316",
                      "Simple Injury":"#eab308","Damage Only":"#22c55e"}
        fig = px.bar(
            dist_sev, x="District", y="Count", color="Severity",
            color_discrete_map=sev_colors, barmode="stack",
            category_orders={"Severity":["Damage Only","Simple Injury","Grievous Injury","Fatal"]},
        )
        fig.update_layout(**CT, height=300, margin=dict(t=10,b=80,l=0,r=0),
                          legend=dict(orientation="h", y=-0.45))
        fig.update_xaxes(tickangle=-35, gridcolor="#1e293b")
        fig.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)

    with bc2:
        sev_pie = df_map["Severity"].astype(str).value_counts().reset_index()
        sev_pie.columns = ["Severity", "Count"]
        fig2 = px.pie(
            sev_pie, names="Severity", values="Count", hole=0.5,
            color="Severity", color_discrete_map=sev_colors,
        )
        fig2.update_layout(**CT, height=300, margin=dict(t=10,b=10,l=0,r=0))
        st.plotly_chart(fig2, use_container_width=True)
