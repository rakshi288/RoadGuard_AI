"""RoadGuard AI — functional homepage."""
import html
import streamlit as st
import plotly.express as px

SCOL = {"Damage Only": "#22c55e", "Simple Injury": "#eab308", "Grievous Injury": "#f97316", "Fatal": "#ef4444"}


def _html(markup):
    # Joining lines prevents Markdown from interpreting indented HTML as code.
    st.markdown(' '.join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def _nav(target):
    st.session_state['goto'] = target
    st.rerun()


def show(df, stats):
    _html('''
    <div style="background:linear-gradient(135deg,#111b46,#19113b);border:1px solid #354383;border-radius:22px;padding:32px 30px;margin-bottom:22px;">
      <div style="font-size:42px;font-weight:900;color:#f8fafc;line-height:1.2;">🛡️ RoadGuard <span style="color:#facc15;">AI</span></div>
      <div style="font-size:17px;color:#c4b5fd;margin-top:10px;">An Intelligent Machine Learning Framework for Road Accident Risk Prediction, Spatial Analysis and Safety Planning</div>
      <div style="margin-top:22px;line-height:2.3;">
        <span style="background:#273565;color:#e0e7ff;padding:8px 12px;border-radius:18px;">🌲 Random Forest</span>&nbsp;
        <span style="background:#164e3a;color:#bbf7d0;padding:8px 12px;border-radius:18px;">🗺️ Karnataka Accident Data</span>&nbsp;
        <span style="background:#55400c;color:#fef08a;padding:8px 12px;border-radius:18px;">📍 31 Administrative Districts</span>
      </div>
      <div style="color:#e2e8f0;font-size:15px;line-height:1.7;margin-top:22px;">Explore severity-based risk indicators, historical accident locations, and road safety recommendations in one interactive application.</div>
    </div>
    ''')
    if st.button('🚀 Get Started — Explore Features', key='home_get_started', type='primary', use_container_width=True):
        _nav('🔴  Risk Prediction')

    st.markdown('### Karnataka Road Accident Dataset')
    a,b,c,d = st.columns(4)
    a.metric('Accident Records', f"{stats.get('total_accidents',len(df)):,}")
    b.metric('Administrative Districts', '31')
    c.metric('Dataset Area Labels', str(stats.get('total_districts',df['DISTRICTNAME'].nunique())))
    d.metric('GPS Records', f"{stats.get('valid_coords',0):,}")
    st.caption('The dataset has separate district/police-jurisdiction labels; these are not all distinct administrative districts.')

    st.markdown('### 🚀 Explore RoadGuard AI')
    cols = st.columns(3)
    cards = [
        ('🔴', 'Accident Risk Prediction', '#ef4444', 'Choose a district and road conditions to obtain a Low, Medium, or High severity-based risk indicator.', '🔴  Risk Prediction', 'home_predict'),
        ('🗺️', 'Spatial Analysis', '#a78bfa', 'Explore recorded accident locations and historical hotspots on an interactive Karnataka map.', '🗺️  Spatial Analysis', 'home_spatial'),
        ('🛡️', 'Safety Planning', '#4ade80', 'Get practical precautions and location-specific suggestions based on selected road conditions.', '🛡️  Safety Planning', 'home_safety'),
    ]
    for col,(emoji,title,color,description,target,key) in zip(cols,cards):
        with col:
            _html(f'''<div style="background:#151b3d;border:1px solid {color};border-radius:18px;padding:24px 17px;min-height:205px;">
            <div style="font-size:34px;">{emoji}</div><div style="font-size:19px;font-weight:800;color:{color};margin:10px 0;">{html.escape(title)}</div>
            <div style="color:#e2e8f0;font-size:14px;line-height:1.6;">{html.escape(description)}</div></div>''')
            if st.button(f'Open {title} →', key=key, use_container_width=True):
                _nav(target)

    st.markdown('### ⚙️ How the Website Works')
    steps = [
        ('1. Select', 'Choose prediction, spatial analysis, or safety planning.'),
        ('2. Enter', 'Select available district, weather, and road features.'),
        ('3. Analyse', 'Python processes inputs using historical data and the trained model.'),
        ('4. Explore', 'Review severity indicators, map locations, and hotspots.'),
        ('5. Plan', 'Read road safety precautions and recommendations.'),
    ]
    for heading,description in steps:
        _html(f'<div style="background:#151b3d;border-left:4px solid #a78bfa;border-radius:10px;padding:12px 17px;margin:8px 0;color:#e2e8f0;"><b style="color:#c4b5fd;">{heading}</b> — {description}</div>')

    st.markdown('### 🚦 Understanding the Three Risk Levels')
    levels = [
        ('🟢 LOW RISK','#22c55e','Damage-only severity category'),
        ('🟡 MEDIUM RISK','#eab308','Simple-injury severity category'),
        ('🔴 HIGH RISK','#ef4444','Grievous or fatal severity category'),
    ]
    for col,(name,color,description) in zip(st.columns(3),levels):
        with col:
            _html(f'<div style="border:1px solid {color};background:#12172f;border-radius:12px;padding:18px 10px;text-align:center;min-height:110px;"><div style="color:{color};font-weight:800;font-size:18px;">{name}</div><div style="color:#e2e8f0;font-size:12px;margin-top:10px;">{description}</div></div>')
    st.info('Scientific note: This model estimates accident severity conditional on an accident occurring. It does not estimate the probability that an accident will happen. Its predictive performance is limited and should be evaluated against a baseline.')

    with st.expander('📊 Historical Data Overview (optional)'):
        left,right = st.columns(2)
        with left:
            if 'Year' in df.columns:
                yearly = df.groupby('Year').size().reset_index(name='Accidents')
                fig = px.bar(yearly,x='Year',y='Accidents',title='Accident records by year')
                fig.update_layout(height=300)
                st.plotly_chart(fig,use_container_width=True)
        with right:
            if 'Severity' in df.columns:
                counts = df['Severity'].astype(str).value_counts().reset_index()
                counts.columns = ['Severity','Count']
                fig = px.pie(counts,names='Severity',values='Count',hole=.45,color='Severity',color_discrete_map=SCOL,title='Recorded severity distribution')
                fig.update_layout(height=300)
                st.plotly_chart(fig,use_container_width=True)
