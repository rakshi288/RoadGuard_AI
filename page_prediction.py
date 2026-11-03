"""RoadGuard AI — Risk Prediction Page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os

from ml_model import (
    train_and_save_model, load_model, load_metrics,
    predict_risk, get_unique_values,
    MODEL_PATH, METRICS_PATH, FEATURES, RISK_LEVELS, SEVERITY_TO_RISK,
)

CT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8")

TIPS = {
    "HIGH RISK": [
        ("d","🚨 High-Severity Risk — Avoid If Possible",
         "This road/environment combination is historically associated with grievous or fatal "
         "accidents in Karnataka. Consider delaying or rerouting."),
        ("d","🛑 Reduce Speed by 40% Minimum",
         "Fatal accidents disproportionately occur on NHs and SHs. Strictly follow posted limits."),
        ("w","🦺 Seatbelt & Helmet Mandatory",
         "Karnataka data shows significantly worse outcomes without protective equipment."),
        ("w","🏥 Emergency Numbers Ready",
         "Police: 100 | Ambulance: 108 | Highway: 1033 | Emergency: 112"),
    ],
    "MEDIUM RISK": [
        ("w","⚠️ Moderate Risk — Heightened Alertness",
         "Conditions associated with simple injury accidents. Standard precautions are adequate."),
        ("w","🚗 Maintain 3-Second Following Distance",
         "Simple injury rear-end collisions are common. Keep safe gap especially in traffic."),
        ("","🚦 Strictly Obey Traffic Rules",
         "Human error causes 79% of Karnataka accidents. No mobile phones while driving."),
        ("","📍 Share Your Route Before Travelling",
         "Inform someone of your route and estimated arrival time."),
    ],
    "LOW RISK": [
        ("","✅ Lower Severity Risk Expected",
         "Conditions associated with property-damage accidents rather than injuries."),
        ("","🔍 Stay Alert in Urban Areas",
         "Watch for parked vehicles, pedestrians, and unmarked speed humps."),
        ("","📋 Document Any Incident Immediately",
         "Photograph scene, exchange insurance details if an accident occurs."),
    ],
}

RISK_EXPLAIN = {
    "HIGH RISK":   ("Grievous Injury or Fatal outcomes are most likely under these conditions "
                    "based on Karnataka historical accident patterns."),
    "MEDIUM RISK": ("Simple Injury outcomes are most likely — moderate severity with potential "
                    "for personal injury."),
    "LOW RISK":    ("Damage Only outcomes are most likely — property damage without serious "
                    "personal injury expected."),
}


def _rc(cls, title, text):
    c = {"d":"rc d","w":"rc w","":"rc"}.get(cls,"rc")
    return f'<div class="{c}"><div class="rct">{title}</div><div class="rcb">{text}</div></div>'


def show(df):
    st.markdown('<div class="ptitle">🔴 Accident Risk Prediction</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="psub">Random Forest model · 2.34 lakh training records · '
        'Predicts severity-based risk: LOW / MEDIUM / HIGH</div>',
        unsafe_allow_html=True,
    )

    # Scientific disclaimer banner
    st.markdown("""
    <div class="ib" style="margin-bottom:1rem;">
        ℹ️ <b style="color:#7c83f5;">What this predicts:</b>
        Given that an accident occurs under these conditions, what severity level is most likely?
        <b style="color:#4ade80">LOW</b> = Damage Only ·
        <b style="color:#fde047">MEDIUM</b> = Simple Injury ·
        <b style="color:#f87171">HIGH</b> = Grievous/Fatal.
        This is a <em>severity-based risk indicator</em>, not a prediction of accident probability.
    </div>""", unsafe_allow_html=True)

    model_ready = os.path.exists(MODEL_PATH) and os.path.exists(METRICS_PATH)

    # ── Model panel ───────────────────────────────────────────────────────────
    with st.expander("⚙️ Model Status & Evaluation Metrics", expanded=not model_ready):
        if model_ready:
            m = load_metrics()
            if m:
                mc1,mc2,mc3,mc4 = st.columns(4)
                mc1.metric("RF Accuracy",      f"{m['rf_accuracy']:.1%}")
                mc2.metric("Macro F1-Score",   f"{m['macro_f1']:.2f}")
                mc3.metric("Baseline Accuracy",f"{m['baseline_accuracy']:.1%}")
                mc4.metric("Training Records", f"{m['train_size']:,}")
                st.caption(
                    "Baseline always predicts HIGH RISK (67% of data). "
                    "RF at 60.1% correctly identifies LOW and MEDIUM cases the baseline misses. "
                    "Macro F1=0.48 on an imbalanced 3-class problem."
                )
                _eval(m)

        ec1,ec2 = st.columns([1,3])
        with ec1:
            if st.button("🔄 Retrain Model", use_container_width=True):
                with st.spinner("Training on 2.93 lakh records (~3 min)…"):
                    try:
                        _,nm = train_and_save_model(df)
                        st.success(f"Done — Accuracy: {nm['rf_accuracy']:.1%}  F1: {nm['macro_f1']:.2f}")
                        st.cache_resource.clear(); st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with ec2:
            st.info(
                "**Features:** District · Weather · Road Type · Surface · Road Character · "
                "Road Condition · Main Cause · Location · Spot · Junction · Hit & Run  \n"
                "**Algorithm:** Random Forest (200 trees, balanced class weights, OrdinalEncoder)"
            )

    if not model_ready:
        st.warning("⚠️ No trained model. Expand panel → **Retrain Model**.")
        return

    model = load_model()
    if model is None:
        st.error("Model file missing. Please retrain."); return

    # ── Input form ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="sh">📋 Step 1 — Select Road & Environment Conditions</div>',
                unsafe_allow_html=True)

    with st.form("risk_form", clear_on_submit=False):
        col1,col2,col3 = st.columns(3)

        with col1:
            st.markdown("**📍 Location**")
            district     = st.selectbox("District",          get_unique_values(df,"DISTRICTNAME"), key="f_dist")
            acc_location = st.selectbox("Accident Location", get_unique_values(df,"Accident_Location"), key="f_loc")
            acc_spot     = st.selectbox("Accident Spot",     get_unique_values(df,"Accident_Spot"), key="f_spot")
            junction     = st.selectbox("Junction Control",  get_unique_values(df,"Junction_Control"), key="f_junc")

        with col2:
            st.markdown("**🌦️ Environment**")
            weather   = st.selectbox("Weather Condition", get_unique_values(df,"Weather"), key="f_weather")
            surface   = st.selectbox("Surface Condition", get_unique_values(df,"Surface_Condition"), key="f_surf")
            road_cond = st.selectbox("Road Condition",    get_unique_values(df,"Road_Condition"), key="f_rcond")
            hit_run   = st.selectbox("Hit & Run",         get_unique_values(df,"Hit_Run"), key="f_hr")

        with col3:
            st.markdown("**🛣️ Road**")
            road_type  = st.selectbox("Road Type",      get_unique_values(df,"Road_Type"), key="f_rtype")
            road_char  = st.selectbox("Road Character", get_unique_values(df,"Road_Character"), key="f_rchar")
            main_cause = st.selectbox("Main Cause",     get_unique_values(df,"Main_Cause"), key="f_cause")

        submitted = st.form_submit_button(
            "🔴 Predict Accident Risk Level", use_container_width=True
        )

    # ── Result ────────────────────────────────────────────────────────────────
    if submitted:
        inputs = {
            "DISTRICTNAME":district,     "Weather":weather,
            "Road_Type":road_type,       "Surface_Condition":surface,
            "Road_Character":road_char,  "Road_Condition":road_cond,
            "Main_Cause":main_cause,     "Accident_Location":acc_location,
            "Accident_Spot":acc_spot,    "Junction_Control":junction,
            "Hit_Run":hit_run,
        }
        try:
            prediction, confidence, proba_dict = predict_risk(model, inputs)
        except Exception as e:
            st.error(f"Prediction error: {e}"); st.exception(e); return

        st.markdown('<div class="sh">📊 Step 2 — Prediction Result</div>', unsafe_allow_html=True)

        css = {"LOW RISK":"rlow","MEDIUM RISK":"rmed","HIGH RISK":"rhigh"}
        emj = {"LOW RISK":"🟢","MEDIUM RISK":"🟡","HIGH RISK":"🔴"}

        st.markdown(f"""
        <div class="rcard {css.get(prediction,'rhigh')}">
            <div class="rbadge">{emj.get(prediction,'🔴')} {prediction}</div>
            <div class="rsub">
                {RISK_EXPLAIN.get(prediction,'')}<br>
                <span style="color:#64748b;font-size:.82rem;">
                    {district} &nbsp;·&nbsp; {road_type} &nbsp;·&nbsp; {weather}
                </span>
            </div>
            <div class="rconf">Model confidence: {confidence:.1%} &nbsp;·&nbsp;
                This is a severity-based risk indicator, not accident probability.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        res1, res2 = st.columns([1,1])

        with res1:
            st.markdown("**Risk Level Probabilities**")
            ro  = ["LOW RISK","MEDIUM RISK","HIGH RISK"]
            bc  = ["#22c55e","#eab308","#ef4444"]
            vs  = [proba_dict.get(r,0.0) for r in ro]
            fig = go.Figure(go.Bar(
                x=ro, y=vs, marker_color=bc,
                text=[f"{v:.1%}" for v in vs], textposition="outside",
            ))
            fig.update_layout(
                **CT, height=250,
                yaxis=dict(range=[0,max(vs)*1.35+.04],tickformat=".0%",gridcolor="#0d1230"),
                xaxis=dict(gridcolor="#0d1230"),
                margin=dict(t=10,b=10,l=0,r=0), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Historical match
            mask = ((df["DISTRICTNAME"]==district) &
                    (df["Road_Type"]==road_type) &
                    (df["Weather"]==weather))
            sim  = df[mask]
            if len(sim) >= 10:
                st.markdown(
                    f"**Historical records — {district} · {road_type} · {weather}:** "
                    f"{len(sim):,} past accidents"
                )
                sc = sim["Severity"].astype(str).value_counts().reset_index()
                sc.columns = ["Severity","Count"]
                sc["Risk"]    = sc["Severity"].map(SEVERITY_TO_RISK)
                sc["Share %"] = (sc["Count"]/sc["Count"].sum()*100).round(1)
                st.dataframe(sc[["Severity","Risk","Count","Share %"]],
                             hide_index=True, use_container_width=True, height=150)
            else:
                st.markdown(f"""
                <div class="ib">
                    Fewer than 10 historical records for {district} + {road_type} + {weather}.
                    Prediction uses patterns from the full 2.34 lakh training records.
                </div>""", unsafe_allow_html=True)

            # Feature importance
            m = load_metrics()
            if m:
                st.markdown("**Top features driving this model**")
                fi = m["feature_importance"]
                fi_df = (fi.reset_index() if hasattr(fi,"reset_index") else fi)
                fi_df.columns = ["Feature","Importance"]
                fig2 = px.bar(
                    fi_df.head(8), x="Importance", y="Feature",
                    orientation="h", color="Importance",
                    color_continuous_scale=["#4338ca","#5b5fc7","#7c83f5"],
                )
                fig2.update_layout(
                    **CT, height=245, coloraxis_showscale=False,
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=5,b=5,l=0,r=0),
                )
                fig2.update_xaxes(gridcolor="#0d1230")
                st.plotly_chart(fig2, use_container_width=True)

        with res2:
            st.markdown("**Safety Recommendations**")
            for cls,title,text in TIPS.get(prediction, TIPS["LOW RISK"]):
                st.markdown(_rc(cls,title,text), unsafe_allow_html=True)

            st.markdown(f"""
            <div class="ib" style="margin-top:.8rem;">
                <b style="color:#94a3b8;">Your selections</b><br>
                {district} · {weather} · {road_type}<br>
                {surface} · {road_char} · {main_cause}<br>
                Hit&amp;Run: {hit_run}
            </div>""", unsafe_allow_html=True)


def _eval(m):
    rows = []
    for c in RISK_LEVELS:
        r = m["classification_report"].get(c,{})
        if r:
            rows.append({"Risk Level":c,
                         "Precision":f"{r['precision']:.2f}",
                         "Recall":f"{r['recall']:.2f}",
                         "F1":f"{r['f1-score']:.2f}",
                         "Support":f"{int(r['support']):,}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True,
                 use_container_width=True, height=150)
    cm  = m["confusion_matrix"]
    lbl = m["labels"]
    fig = px.imshow(cm, x=lbl, y=lbl,
                    color_continuous_scale="Purples",
                    text_auto=True,
                    labels=dict(x="Predicted",y="Actual"),
                    title="Confusion Matrix")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8", height=270, margin=dict(t=30,b=20,l=0,r=0),
    )
    st.plotly_chart(fig, use_container_width=True)
