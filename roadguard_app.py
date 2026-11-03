"""RoadGuard AI — Main Streamlit Application"""
import streamlit as st

st.set_page_config(
    page_title="RoadGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*, html, body, [class*="css"] { font-family:'Inter',sans-serif; }

/* ── Background ── */
.stApp { background:#05071a; }
.main .block-container { padding:1.2rem 2rem 2.5rem; max-width:1360px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#070a20 0%,#0b0f2e 60%,#0f1328 100%);
    border-right:1px solid #1a2550;
}
section[data-testid="stSidebar"] * { color:#c4cde0 !important; }

/* ── Buttons ── */
.stButton>button {
    background:linear-gradient(135deg,#5b5fc7,#4338ca) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    padding:.5rem 1.4rem !important; font-weight:600 !important;
    font-size:.9rem !important; width:100% !important; transition:all .18s !important;
}
.stButton>button:hover {
    background:linear-gradient(135deg,#7c3aed,#5b5fc7) !important;
    box-shadow:0 4px 18px rgba(91,95,199,.5) !important;
    transform:translateY(-1px) !important;
}

/* ── Metrics ── */
div[data-testid="stMetricValue"] { font-size:1.55rem !important; font-weight:700 !important; color:#f1f5f9 !important; }
div[data-testid="stMetricLabel"] { color:#475569 !important; font-size:.73rem !important; }

/* ── Inputs ── */
.stSelectbox>label, .stMultiSelect>label { color:#94a3b8 !important; font-size:.8rem !important; }
div[data-baseweb="select"]>div { background:#0d1230 !important; border-color:#1a2550 !important; color:#e2e8f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:.4rem; background:transparent; border-bottom:1px solid #1a2550; }
.stTabs [data-baseweb="tab"] { background:transparent; border:none; border-radius:8px 8px 0 0;
    color:#475569 !important; padding:.45rem 1.1rem; font-size:.85rem; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#5b5fc7,#4338ca) !important;
    color:#fff !important; }

/* ── Expander ── */
details>summary { color:#64748b !important; font-size:.85rem !important; }

/* ── Misc ── */
#MainMenu, footer, header { visibility:hidden; }
hr { border-color:#1a2550; }

/* ── KPI Card ── */
.kcard {
    background:linear-gradient(135deg,#0b0f2e,#0d1230);
    border:1px solid #1a2550; border-radius:14px;
    padding:1rem 1.1rem; text-align:center; height:108px;
    display:flex; flex-direction:column; justify-content:center;
    transition:transform .18s, box-shadow .18s;
}
.kcard:hover { transform:translateY(-3px); box-shadow:0 8px 28px rgba(91,95,199,.22); }
.ki { font-size:1.55rem; margin-bottom:.12rem; }
.kv { font-size:1.6rem; font-weight:800; color:#f1f5f9; margin:0; }
.kl { font-size:.65rem; color:#334155; text-transform:uppercase; letter-spacing:.08em; margin:0; }

/* ── Page title ── */
.ptitle { font-size:1.85rem; font-weight:900;
    background:linear-gradient(135deg,#7c83f5,#a78bfa,#c084fc);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:.08rem; }
.psub { color:#334155; font-size:.82rem; margin-bottom:1.1rem; }

/* ── Section header ── */
.sh { font-size:1.05rem; font-weight:700; color:#e2e8f0;
    border-left:3px solid #5b5fc7; padding-left:.65rem;
    margin:1rem 0 .65rem; }

/* ── Risk cards ── */
.rcard { border-radius:16px; padding:1.8rem 1.6rem; text-align:center; margin:1rem 0; }
.rlow  { background:linear-gradient(135deg,#011c0a,#022d14); border:2px solid #22c55e; }
.rmed  { background:linear-gradient(135deg,#1a1100,#2d1e00); border:2px solid #eab308; }
.rhigh { background:linear-gradient(135deg,#1a0404,#380808); border:2px solid #ef4444; }
.rbadge { font-size:2.4rem; font-weight:900; }
.rlow .rbadge  { color:#4ade80; }
.rmed .rbadge  { color:#fde047; }
.rhigh .rbadge { color:#f87171; }
.rsub  { font-size:.88rem; color:#94a3b8; margin-top:.4rem; }
.rconf { font-size:.78rem; color:#475569; margin-top:.22rem; }

/* ── Rec cards ── */
.rc { background:#0c1535; border:1px solid #1a2550; border-left:4px solid #5b5fc7;
    border-radius:10px; padding:.75rem .95rem; margin-bottom:.5rem; }
.rc.w { border-color:#f97316; border-left-color:#f97316;
    background:linear-gradient(135deg,#1c0a00,#0c1535); }
.rc.d { border-color:#ef4444; border-left-color:#ef4444;
    background:linear-gradient(135deg,#190303,#0c1535); }
.rct { font-weight:600; color:#e2e8f0; font-size:.86rem; }
.rcb { color:#475569; font-size:.78rem; margin-top:.15rem; line-height:1.45; }

/* ── Feature cards ── */
.fc {
    background:linear-gradient(145deg,#0b0f2e,#0d1438);
    border:1px solid #1a2550; border-radius:16px;
    padding:1.8rem 1.5rem; height:260px;
    display:flex; flex-direction:column; justify-content:space-between;
    transition:transform .2s, box-shadow .2s, border-color .2s;
}
.fc:hover { transform:translateY(-5px); box-shadow:0 12px 40px rgba(91,95,199,.3); border-color:#5b5fc7; }
.fci  { font-size:2.6rem; margin-bottom:.4rem; }
.fct  { font-size:1.08rem; font-weight:700; color:#e2e8f0; margin-bottom:.35rem; }
.fcd  { font-size:.8rem; color:#475569; line-height:1.5; flex-grow:1; }

/* ── Info box ── */
.ib { background:#0c1535; border:1px solid #1a2550; border-radius:10px;
    padding:.75rem 1rem; font-size:.78rem; color:#334155; }

/* ── Step card ── */
.step {
    background:linear-gradient(135deg,#0b0f2e,#0d1230);
    border:1px solid #1a2550; border-radius:14px;
    padding:1.2rem 1rem; text-align:center; height:165px;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
}
.stepn { width:32px; height:32px; border-radius:50%;
    background:linear-gradient(135deg,#5b5fc7,#4338ca);
    color:#fff; font-weight:800; font-size:.95rem;
    display:flex; align-items:center; justify-content:center; margin-bottom:.5rem; }
.stept { font-size:.88rem; font-weight:700; color:#e2e8f0; margin-bottom:.25rem; }
.stepd { font-size:.72rem; color:#475569; line-height:1.4; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1.3rem 0 1.1rem;'>
        <div style='font-size:2.8rem;'>🛡️</div>
        <div style='font-size:1.15rem;font-weight:800;
                    background:linear-gradient(135deg,#7c83f5,#a78bfa);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            RoadGuard AI
        </div>
        <div style='font-size:.65rem;color:#1a2550;margin-top:.2rem;'>
            Karnataka · ML Road Safety System
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

with st.sidebar:
    # Existing sidebar logo code stays here

    pages = [
        "🏠  Home",
        "🔴  Risk Prediction",
        "🗺️  Spatial Analysis",
        "🛡️  Safety Planning",
        "📊  Analytics",
    ]

    if "goto" in st.session_state:
        target = st.session_state.pop("goto")
        if target in pages:
            st.session_state["nav"] = target

    page = st.radio(
        "nav",
        pages,
        key="nav",
        label_visibility="collapsed"
    )

    # Existing sidebar content continues here

    st.markdown("""
    <hr>
    <div style='font-size:.63rem;color:#1a2550;text-align:center;padding:.3rem 0;line-height:1.7;'>
        Karnataka Accident Dataset<br>2.93L Records · 38 Districts<br>2016 – 2023
    </div>
    """, unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
from data_loader import load_data, get_summary_stats
with st.spinner("Loading dataset…"):
    df    = load_data()
    stats = get_summary_stats()

# ── Handle card navigation ────────────────────────────────────────────────────
if "goto" in st.session_state:
    page = st.session_state.pop("goto")

# ── Route ─────────────────────────────────────────────────────────────────────
if page == "🏠  Home":
    import page_home as pg;       pg.show(df, stats)
elif page == "🔴  Risk Prediction":
    import page_prediction as pg; pg.show(df)
elif page == "🗺️  Spatial Analysis":
    import page_spatial as pg;    pg.show(df)
elif page == "🛡️  Safety Planning":
    import page_safety as pg;     pg.show(df)
elif page == "📊  Analytics":
    import page_analytics as pg;  pg.show(df, stats)
