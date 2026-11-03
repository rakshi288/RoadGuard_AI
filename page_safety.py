"""RoadGuard AI — Safety Planning Page"""
import streamlit as st
import plotly.express as px
import pandas as pd
from data_loader import load_data

CT   = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8")
SCOL = {"Damage Only":"#22c55e","Simple Injury":"#eab308","Grievous Injury":"#f97316","Fatal":"#ef4444"}

WEATHER_RULES = {
    "Foggy":[
        ("danger","🌫️ Critical: Fog — Reduce Speed ≥40%",
         "Fog has among the highest fatal rates in Karnataka data. Use low-beam + fog lights. "
         "Never use high beams — they reflect off fog and blind oncoming drivers."),
        ("warn","🚗 4-Second Following Gap",
         "Reaction distance doubles in fog. Maintain at least 4 seconds gap from the vehicle ahead."),
        ("warn","📻 Check Traffic Advisory: 1033","Always check Karnataka highway advisories before travelling in foggy conditions."),
    ],
    "Rainy":[
        ("danger","🌧️ Wet Road — Tyre Grip Reduced 30%",
         "Rain significantly increases severity in Karnataka accident data. Stay below 60 km/h to avoid hydroplaning."),
        ("warn","🔦 Wiper & Tyre Check","Ensure wipers work. Check tyre tread depth. Low tread in rain is extremely dangerous."),
        ("","🌊 Avoid Flooded Roads","Never attempt flooded roads or rivulets. Flash floods are common in Karnataka hills."),
    ],
    "Clear":[
        ("warn","☀️ Sun Glare at Dawn/Dusk","Clear-sky accidents often involve sun glare. Keep polarised sunglasses available."),
        ("","🚗 Beware Speed Complacency","Clear conditions encourage over-speeding. Most NH fatalities in Karnataka occur on clear days."),
    ],
    "Extreme Heat":[
        ("warn","🌡️ Tyre Blowout Risk","High temperatures raise tyre pressure. Check tyre pressure in the morning."),
        ("warn","😴 Driver Fatigue Warning","Heat accelerates fatigue. Take a break every 2 hours and stay hydrated."),
    ],
    "Extreme Cold":[
        ("warn","🥶 Black Ice Possible","Cold mornings in Malnad/Kodagu can cause black ice. Avoid dawn travel on hilly routes."),
    ],
    "Windy":[
        ("danger","💨 Two-Wheeler Emergency","Strong winds are a leading cause of two-wheeler accidents. Reduce speed; never overtake in crosswinds."),
        ("warn","🚛 High-Sided Vehicle Danger","Trucks can be blown sideways. Increase lateral clearance on bridges and open highways."),
    ],
    "Cloudy":[("","☁️ Standard — Watch for Rain","Watch for sudden rain or fog, especially in hilly districts.")],
    "Snow/Ice":[("danger","❄️ Severe Traction Loss","Avoid travel unless absolutely necessary. Use chains if available.")],
    "Dust Storm":[("danger","🌪️ Near-Zero Visibility","Pull off the road completely and wait for the storm to pass. Do not drive through.")],
}

ROAD_RULES = {
    "Curve":[
        ("danger","↩️ Blind Curve — Slow Down Before Entry",
         "Curves are disproportionately fatal in Karnataka. Reduce speed before — not in — the curve. Never overtake."),
        ("warn","📢 Sound Horn on Blind Curves","On narrow roads, sound horn before blind curves to warn oncoming traffic."),
    ],
    "Sharp Curve":[
        ("danger","🔴 Sharp Curve — Extreme Hazard","Reduce to ≤30 km/h before the apex. Absolutely no overtaking."),
        ("warn","🚫 No Passing Zone","Oncoming vehicles have no room to react. Even slow vehicles cannot pass safely."),
    ],
    "Incline":[
        ("warn","⛰️ Engine Braking on Descents","Use lower gears going down. Brake fade causes serious accidents on Karnataka ghat roads."),
        ("warn","🚛 Runaway Truck Risk","Stay well clear of heavy vehicles on steep descents."),
    ],
    "Steep Incline or Climb":[("danger","⛰️ Steep Gradient — Test Brakes","Brake failure risk is high. Test brakes frequently on long descents.")],
    "Straight and flat":[
        ("warn","🛣️ Straight Road Speed Trap","Straight roads cause over-confidence. Most NH fatalities in Karnataka occur on straight sections."),
        ("","😴 Highway Hypnosis","Long straight drives cause fatigue. Take a break every 2 hours."),
    ],
    "Hump":[("","🏙️ Speed Hump Awareness","Many speed humps are unmarked on Karnataka city/village roads. Stay alert.")],
    "Crest of hill":[("danger","⚠️ Hidden Approach","Never overtake approaching a crest — vehicles beyond cannot be seen.")],
    "Dip or trough":[("warn","🌊 Flood Water Risk","Dips collect rainwater. Never drive through standing water of unknown depth.")],
    "Curve and Incline":[("danger","↩️⛰️ Combined Hazard","Blind approach + gradient = extreme danger. Reduce speed significantly.")],
    "Slight Curve":[("","↩️ Mild Curve","Lower risk but reduce speed at night and in adverse weather.")],
    "Gentle Incline or Climb":[("","🔼 Gentle Gradient","Check brakes and fluid levels before hilly travel.")],
}

ROAD_IMPROVEMENTS = {
    "Curve":       ["Install chevron markers and guardrails","Add warning signs 200 m before curve","Install solar studs on road edges"],
    "Sharp Curve": ["Install crash barriers","Add speed limit signs with enforcement","Install warning lights at night"],
    "Incline":     ["Install runaway truck ramps","Add brake check points","Install gradient warning signs"],
    "Hump":        ["Clearly paint all speed humps yellow/white","Add advance warning signs"],
    "Crest of hill":["Install convex mirrors","Add do-not-overtake markings","Install rumble strips"],
}

SPEED_RECS = {
    "NH":              "Recommended: ≤80 km/h (heavy vehicles ≤60 km/h)",
    "State Highway":   "Recommended: ≤70 km/h in clear weather, ≤50 km/h at night",
    "City or Town Road":"Recommended: ≤40 km/h in urban areas",
    "Village Road":    "Recommended: ≤30 km/h — watch for pedestrians and animals",
    "Two way":         "Recommended: ≤60 km/h — maintain centre line discipline",
}

HIGH_RISK = {"Bengaluru City","Tumakuru","Bengaluru Dist","Hassan","Mandya",
             "Belagavi Dist","Chitradurga","Shivamogga","Mysuru Dist","Ramanagara"}

GENERAL = [
    ("warn","🦺 Seatbelt & Helmet Always",
     "Karnataka data shows significantly worse outcomes without protective equipment."),
    ("warn","📵 No Phone While Driving",
     "Human error causes 79% of Karnataka accidents. Use hands-free or pull over safely."),
    ("","🌙 Night Travel — Use High Beams","Fatal risk is higher at night. Watch for pedestrians and animals."),
    ("","🚛 50 m Distance from Trucks","NHs carry heavy traffic. Maintain distance especially on curves."),
    ("","🏥 Emergency Numbers",
     "Police: 100 | Ambulance: 108 | Highway: 1033 | Emergency: 112"),
]


@st.cache_data(show_spinner=False)
def _stats(district):
    df  = load_data()
    sub = df[df["DISTRICTNAME"] == district]
    if sub.empty: return None
    sev = sub["Severity"].astype(str)
    return {
        "total":     len(sub),
        "fatal":     int((sev=="Fatal").sum()),
        "fatal_pct": (sev=="Fatal").mean()*100,
        "griev_pct": (sev=="Grievous Injury").mean()*100,
        "top3_spots":sub["Accident_Spot"].value_counts().head(3).index.tolist(),
        "top3_roads":sub["Road_Type"].value_counts().head(3).index.tolist(),
        "fatal_weather":sub[sev=="Fatal"]["Weather_Clean"].value_counts().head(2).index.tolist(),
        "fatal_rchar":  sub[sev=="Fatal"]["Road_Character"].value_counts().head(2).index.tolist(),
        "yr_fatal":  sub[sev=="Fatal"].groupby("Year").size().reset_index(name="Fatal"),
        "peak_year": int(sub["Year"].value_counts().idxmax()),
        "top_cause": sub["Main_Cause"].value_counts().idxmax(),
    }


@st.cache_data(show_spinner=False)
def _rt_fatal(district):
    df  = load_data()
    sub = df[df["DISTRICTNAME"] == district]
    rt  = sub.groupby("Road_Type").agg(
            Total=("Severity","count"),
            Fatal=("Severity",lambda x:(x.astype(str)=="Fatal").sum()),
          ).reset_index()
    rt  = rt[rt["Total"] >= 50]
    rt["Fatal %"] = (rt["Fatal"]/rt["Total"]*100).round(1)
    return rt.sort_values("Fatal %", ascending=False).head(8)


def _rec(ct, title, text):
    # ct: "danger"->"d", "warn"->"w", ""->""
    m = {"danger":"d","warn":"w","":""}
    cls = m.get(ct, ct)
    extra = f" {cls}" if cls else ""
    return (f'<div class="rc{extra}">'
            f'<div class="rct">{title}</div>'
            f'<div class="rcb">{text}</div></div>')


def show(df):
    st.markdown('<div class="ptitle">🛡️ Road Safety Planning</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="psub">Select district and travel conditions — '
        'get a personalised, data-backed safety plan</div>',
        unsafe_allow_html=True,
    )

    # ── Input panel ───────────────────────────────────────────────────────────
    st.markdown('<div class="sh">🔍 Configure Your Safety Plan</div>', unsafe_allow_html=True)

    districts     = sorted(df["DISTRICTNAME"].dropna().unique().tolist())
    weather_opts  = sorted([w for w in df["Weather_Clean"].dropna().unique()
                            if w not in ("Not Applicable","Others")])
    road_opts     = sorted([r for r in df["Road_Character"].dropna().unique()
                            if r not in ("Not Applicable","Others")])
    road_type_opts= sorted([r for r in df["Road_Type"].dropna().unique()
                            if r not in ("Not Applicable","Others")])

    ic1,ic2,ic3,ic4 = st.columns(4)
    with ic1: sel_dist  = st.selectbox("📍 District",       districts,       key="sf_dist")
    with ic2: sel_w     = st.selectbox("🌦️ Weather",        weather_opts,    key="sf_w")
    with ic3: sel_rchar = st.selectbox("↩️ Road Character", road_opts,       key="sf_rchar")
    with ic4: sel_rtype = st.selectbox("🛣️ Road Type",      road_type_opts,  key="sf_rtype")

    gc,_ = st.columns([1,4])
    with gc:
        if st.button("🛡️ Get Safety Plan", use_container_width=True, key="sf_gen"):
            st.session_state["sf_plan"] = dict(
                district=sel_dist, weather=sel_w,
                road_char=sel_rchar, road_type=sel_rtype,
            )

    plan = st.session_state.get("sf_plan")
    if not plan:
        st.markdown("""
        <div style="background:#0d1230;border:1px dashed #1e2d5a;border-radius:14px;
                    padding:2.5rem;text-align:center;margin-top:1rem;">
            <div style="font-size:2.5rem;margin-bottom:.6rem;">🛡️</div>
            <div style="color:#475569;font-size:.9rem;">
                Select your district and travel conditions above,<br>
                then click <b style="color:#818cf8">Get Safety Plan</b> to receive
                personalised recommendations.
            </div>
        </div>""", unsafe_allow_html=True)
        return

    district  = plan["district"]
    weather   = plan["weather"]
    road_char = plan["road_char"]
    road_type = plan["road_type"]
    stats     = _stats(district)

    if not stats:
        st.warning(f"No data for {district}."); return

    st.markdown("---")

    # ── Risk banner ───────────────────────────────────────────────────────────
    if district in HIGH_RISK:
        st.markdown(f"""
        <div class="rc danger">
            <div class="rc-title" style="font-size:1rem;">🔴 HIGH-RISK DISTRICT: {district}</div>
            <div class="rc-text" style="font-size:.85rem;">
                {district} is among Karnataka's top 10 accident-prone districts.
                <b>{stats['fatal']:,} fatal accidents</b> ({stats['fatal_pct']:.1f}% of all accidents)
                recorded 2016–2023.
            </div>
        </div>""", unsafe_allow_html=True)

    # KPIs
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total Accidents", f"{stats['total']:,}")
    k2.metric("Fatal Count",     f"{stats['fatal']:,}")
    k3.metric("Fatal Rate",      f"{stats['fatal_pct']:.1f}%")
    k4.metric("Grievous Rate",   f"{stats['griev_pct']:.1f}%")

    st.markdown("---")
    st.markdown('<div class="sh">⚠️ District Risk Factors (from real Karnataka data)</div>',
                unsafe_allow_html=True)

    dw1,dw2 = st.columns(2)
    with dw1:
        spots_str = ", ".join(stats["top3_spots"])
        st.markdown(_rec("warn","📌 Most Dangerous Accident Spots",
            f"Historical data: most accidents in {district} occur at <b>{spots_str}</b>."),
            unsafe_allow_html=True)
        fw = ", ".join(stats["fatal_weather"]) or "N/A"
        st.markdown(_rec("warn","🌦️ Deadliest Weather Conditions",
            f"Most fatal accidents in {district} occurred during <b>{fw}</b> conditions."),
            unsafe_allow_html=True)
    with dw2:
        roads_str = ", ".join(stats["top3_roads"])
        match = " ⚠️ Matches your road type." if road_type in stats["top3_roads"] else ""
        st.markdown(_rec("warn","🛣️ High-Accident Road Types",
            f"Highest volumes on <b>{roads_str}</b>.{match}"),
            unsafe_allow_html=True)
        frc   = ", ".join(stats["fatal_rchar"]) or "N/A"
        match2= f" ⚠️ Matches your selection ({road_char})." if road_char in stats["fatal_rchar"] else ""
        st.markdown(_rec("warn","↩️ Fatal Road Characters",
            f"Most fatals on <b>{frc}</b>.{match2}"),
            unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sh">📋 Personalised Recommendations</div>', unsafe_allow_html=True)

    rc1,rc2 = st.columns(2)
    with rc1:
        st.markdown(f"**🌦️ {weather} Weather**")
        for ct,title,text in WEATHER_RULES.get(weather,[
            ("","✅ Standard Conditions","Follow standard road safety rules. No specific weather alerts.")
        ]):
            st.markdown(_rec(ct,title,text), unsafe_allow_html=True)

    with rc2:
        st.markdown(f"**↩️ {road_char} Road**")
        for ct,title,text in ROAD_RULES.get(road_char,[
            ("","✅ Standard Road","No specific road character alerts for this selection.")
        ]):
            st.markdown(_rec(ct,title,text), unsafe_allow_html=True)

    # Speed management
    st.markdown("---")
    speed_rec = SPEED_RECS.get(road_type, "Follow posted speed limit signs.")
    st.markdown(f"""
    <div class="rc">
        <div class="rc-title">⚡ Speed Management — {road_type}</div>
        <div class="rc-text">{speed_rec}</div>
    </div>""", unsafe_allow_html=True)

    # Road improvement suggestions
    improvements = ROAD_IMPROVEMENTS.get(road_char)
    if improvements:
        impr_html = "".join(f"• {i}<br>" for i in improvements)
        st.markdown(f"""
        <div class="rc">
            <div class="rc-title">🔧 Suggested Road Infrastructure Improvements — {road_char}</div>
            <div class="rc-text">{impr_html}</div>
        </div>""", unsafe_allow_html=True)

    # Charts
    st.markdown("---")
    cc1,cc2 = st.columns(2)
    with cc1:
        st.markdown(f"**📈 Fatal Trend — {district}**")
        if not stats["yr_fatal"].empty:
            fig = px.line(stats["yr_fatal"], x="Year", y="Fatal",
                          markers=True, color_discrete_sequence=["#ef4444"])
            fig.update_layout(**CT, height=210, margin=dict(t=5,b=5,l=0,r=0))
            fig.update_xaxes(gridcolor="#0d1230")
            fig.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig, use_container_width=True)

    with cc2:
        st.markdown(f"**🛣️ Road Type Fatal Rate — {district}**")
        rt = _rt_fatal(district)
        if not rt.empty:
            fig2 = px.bar(rt, x="Road_Type", y="Fatal %",
                          color="Fatal %",
                          color_continuous_scale=["#6366f1","#f97316","#ef4444"])
            fig2.update_layout(**CT, height=210, coloraxis_showscale=False,
                               margin=dict(t=5,b=70,l=0,r=0))
            fig2.update_xaxes(tickangle=-35, gridcolor="#0d1230")
            fig2.update_yaxes(gridcolor="#0d1230")
            st.plotly_chart(fig2, use_container_width=True)

    # General guidelines
    st.markdown("---")
    st.markdown('<div class="sh">📋 General Karnataka Road Safety</div>', unsafe_allow_html=True)
    gc2 = st.columns(2)
    for i,(ct,title,text) in enumerate(GENERAL):
        gc2[i%2].markdown(_rec(ct,title,text), unsafe_allow_html=True)

    # Treemap
    st.markdown("---")
    st.markdown('<div class="sh">🗺️ Karnataka District Risk Overview</div>', unsafe_allow_html=True)
    dr = load_data().groupby("DISTRICTNAME").agg(
            Total=("Severity","count"),
            Fatal=("Severity",lambda x:(x.astype(str)=="Fatal").sum()),
         ).reset_index()
    dr["Fatal %"] = (dr["Fatal"]/dr["Total"]*100).round(1)
    fig_tm = px.treemap(
        dr.sort_values("Fatal %",ascending=False).head(30),
        path=["DISTRICTNAME"], values="Total", color="Fatal %",
        color_continuous_scale=["#22c55e","#eab308","#f97316","#ef4444"],
        title="Size = Total Accidents · Colour = Fatal Rate %",
    )
    fig_tm.update_layout(**CT, height=400, margin=dict(t=40,b=5,l=0,r=0))
    st.plotly_chart(fig_tm, use_container_width=True)
