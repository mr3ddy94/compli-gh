import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.database import get_supabase_client

# Page configuration
st.set_page_config(
    page_title="CompliGH - Ghana Fintech Compliance",
    page_icon="🇬🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# IMPROVED Custom CSS - Better readability and modern design
st.markdown("""
    <style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background - soft light gray */
    .main {
        background-color: #F8F9FA;
    }
    
    /* Sidebar styling - dark professional */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] * {
        color: #F1F5F9 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #FCD116 !important;
        font-weight: 700;
    }
    
    /* Metric cards - clean white cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Buttons - Ghana red with hover */
    .stButton>button {
        background: linear-gradient(135deg, #CE1126 0%, #9A0D1C 100%);
        color: white;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        box-shadow: 0 2px 8px rgba(206, 17, 38, 0.2);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #9A0D1C 0%, #CE1126 100%);
        box-shadow: 0 4px 12px rgba(206, 17, 38, 0.35);
        transform: translateY(-2px);
    }
    
    /* Headers - better hierarchy */
    h1 {
        color: #1e293b !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em !important;
    }
    
    h2 {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
    }
    
    /* Progress bars - Ghana colors */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #CE1126 0%, #FCD116 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background-color: #E2E8F0;
        border-radius: 10px;
    }
    
    /* Expanders - clean card style */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: #1e293b;
        font-size: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #CBD5E1;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 1.5rem;
    }
    
    /* Success/Warning/Error boxes - softer colors */
    .stSuccess {
        background-color: #ECFDF5;
        border-left: 4px solid #10B981;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: #065F46;
    }
    
    .stWarning {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: #92400E;
    }
    
    .stError {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: #991B1B;
    }
    
    .stInfo {
        background-color: #DBEAFE;
        border-left: 4px solid #3B82F6;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: #1E40AF;
    }
    
    /* Tabs - modern style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #64748b;
        background-color: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #CE1126;
        color: white;
    }
    
    /* Data frames - clean table style */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Text - better readability */
    p, .stMarkdown {
        color: #475569;
        line-height: 1.7;
        font-size: 1rem;
    }
    
    .stCaption {
        color: #94A3B8;
        font-size: 0.875rem;
    }
    
    /* Cards effect */
    div[data-testid="column"] > div {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    
    div[data-testid="column"] > div:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }
    
    /* Horizontal rule */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
    }
    
    /* Container spacing */
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Plotly chart styling */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'organization_name' not in st.session_state:
    st.session_state.organization_name = "Demo Fintech Ltd"
if 'compliance_score' not in st.session_state:
    st.session_state.compliance_score = 87

# Sidebar - improved design
with st.sidebar:
    st.markdown("# 🇬🇭 CompliGH")
    st.markdown("##### *Ghana Fintech Compliance*")
    st.markdown("---")
    
    # Organization info box
    st.markdown("### 📊 Organization")
    st.info(f"**{st.session_state.organization_name}**")
    
    st.markdown("### 📈 Compliance Score")
    score = st.session_state.compliance_score
    
    # Color-coded score display
    if score >= 80:
        st.success(f"## {score}%\n**Excellent**")
    elif score >= 60:
        st.warning(f"## {score}%\n**Good**")
    else:
        st.error(f"## {score}%\n**Needs Attention**")
    
    st.markdown("---")
    
    # Quick stats in sidebar
    st.markdown("### 🎯 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Frameworks", "6", label_visibility="visible")
    with col2:
        st.metric("Items", "36", label_visibility="visible")
    
    st.markdown("---")
    
    # Version info
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #94A3B8;'>
            <small>Version 1.0.0</small><br>
            <small>© 2026 CompliGH</small>
        </div>
    """, unsafe_allow_html=True)

# Main content
st.title("📊 Compliance Dashboard")
st.markdown("##### Real-time monitoring for Ghanaian fintech regulations")
st.markdown("")  # spacing

# Top metrics row with improved cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Compliance Score",
        value="87%",
        delta="↑ 5%",
        delta_color="normal",
        help="Overall compliance across all frameworks"
    )

with col2:
    st.metric(
        label="Active Regulations",
        value="36",
        delta="8 need attention",
        delta_color="inverse",
        help="Total compliance items being tracked"
    )

with col3:
    st.metric(
        label="Risk Level",
        value="Low",
        delta="↓ 2 points",
        delta_color="normal",
        help="Current risk assessment score"
    )

with col4:
    st.metric(
        label="Next Audit",
        value="14 days",
        delta="Q1 BoG Report",
        help="Upcoming regulatory deadline"
    )

st.markdown("---")

# Main layout - two columns with better spacing
col_main, col_side = st.columns([2, 1], gap="large")

with col_main:
    st.markdown("## 📋 Compliance Frameworks Overview")
    st.markdown("")
    
    # Framework summary with better visual hierarchy
    frameworks = {
        "🏦 Bank of Ghana": {"total": 22, "compliant": 18, "warning": 3, "critical": 1, "score": 82, "color": "#10B981"},
        "💰 AML/CFT": {"total": 13, "compliant": 10, "warning": 2, "critical": 1, "score": 77, "color": "#F59E0B"},
        "🔒 Data Protection Act": {"total": 9, "compliant": 8, "warning": 1, "critical": 0, "score": 89, "color": "#10B981"},
        "💳 Payment Systems Act": {"total": 8, "compliant": 7, "warning": 1, "critical": 0, "score": 88, "color": "#10B981"},
        "🔐 ISO 27001": {"total": 8, "compliant": 5, "warning": 2, "critical": 1, "score": 63, "color": "#F59E0B"},
        "💳 PCI DSS": {"total": 6, "compliant": 5, "warning": 1, "critical": 0, "score": 83, "color": "#10B981"}
    }
    
    for framework, stats in frameworks.items():
        # Determine badge color
        if stats['score'] >= 80:
            badge = "🟢 Compliant"
        elif stats['score'] >= 60:
            badge = "🟡 Review Needed"
        else:
            badge = "🔴 Action Required"
            
        with st.expander(f"{framework} — **{stats['score']}%** — {badge}", expanded=False):
            # Metrics in clean layout
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)
            fcol1.metric("📊 Total", stats['total'])
            fcol2.metric("✅ Compliant", stats['compliant'])
            fcol3.metric("⚠️ Warning", stats['warning'])
            fcol4.metric("❌ Critical", stats['critical'])
            
            st.markdown("")
            
            # Progress bar with percentage
            st.progress(stats['score'] / 100)
            st.markdown(f"<div style='text-align: right; color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;'>{stats['score']}% Complete</div>", unsafe_allow_html=True)
            
            st.markdown("")
            
            # Action buttons with better spacing
            acol1, acol2, acol3 = st.columns([1, 1, 1])
            with acol1:
                if st.button(f"📝 View Details", key=f"view_{framework}", use_container_width=True):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol2:
                if st.button(f"🔄 Update Status", key=f"update_{framework}", use_container_width=True):
                    st.info("✨ Status update feature coming soon!")
            with acol3:
                if st.button(f"📎 Documents", key=f"docs_{framework}", use_container_width=True):
                    st.info("📁 Document management coming soon!")

with col_side:
    # Risk gauge with better styling
    st.markdown("## ⚠️ Risk Assessment")
    st.markdown("")
    
    risk_score = 32
    
    # Create a more modern gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Risk Score</b>", 'font': {'size': 18, 'color': '#1e293b'}},
        number={'font': {'size': 48, 'color': '#1e293b'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#CBD5E1"},
            'bar': {'color': "#CE1126", 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 30], 'color': '#D1FAE5'},
                {'range': [30, 60], 'color': '#FEF3C7'},
                {'range': [60, 100], 'color': '#FEE2E2'}
            ],
            'threshold': {
                'line': {'color': "#1e293b", 'width': 4},
                'thickness': 0.8,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font={'color': "#1e293b", 'family': "Inter"},
        height=280,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk level badge with better styling
    if risk_score < 30:
        st.success("✅ **Low Risk** — System is secure")
    elif risk_score < 60:
        st.warning("⚠️ **Medium Risk** — Review needed")
    else:
        st.error("🚨 **High Risk** — Immediate action required")
    
    st.markdown("---")
    
    # Upcoming deadlines with better visual hierarchy
    st.markdown("## 📅 Upcoming Deadlines")
    st.markdown("")
    
    deadlines = [
        {"task": "Quarterly BoG Report", "days": 14, "status": "urgent", "icon": "⏰"},
        {"task": "AML Risk Assessment", "days": 28, "status": "normal", "icon": "📋"},
        {"task": "DPC Annual Filing", "days": 45, "status": "normal", "icon": "📄"},
        {"task": "ISO 27001 Audit", "days": 60, "status": "normal", "icon": "🔐"}
    ]
    
    for deadline in deadlines:
        if deadline['status'] == 'urgent':
            st.warning(f"**{deadline['icon']} {deadline['task']}**\n\n⏱️ Due in **{deadline['days']} days**")
        else:
            st.info(f"**{deadline['icon']} {deadline['task']}**\n\n📆 Due in {deadline['days']} days")
        st.markdown("")

st.markdown("---")

# Recent activity with improved table design
st.markdown("## 📜 Recent Activity")
st.markdown("##### Latest compliance actions across your organization")
st.markdown("")

# Create a more visual activity log
recent_logs = [
    {"time": "2 hours ago", "action": "Updated CDD status", "user": "John Mensah", "type": "update"},
    {"time": "5 hours ago", "action": "Uploaded AML policy document", "user": "Ama Kwakye", "type": "upload"},
    {"time": "Yesterday", "action": "Completed ISO 27001 training", "user": "Kofi Asante", "type": "complete"},
    {"time": "2 days ago", "action": "Generated compliance report", "user": "John Mensah", "type": "report"}
]

# Display as styled cards
for i, log in enumerate(recent_logs):
    col1, col2, col3 = st.columns([2, 5, 2])
    
    with col1:
        st.markdown(f"<div style='color: #94A3B8; font-size: 0.875rem;'>{log['time']}</div>", unsafe_allow_html=True)
    
    with col2:
        icon = {"update": "🔄", "upload": "📤", "complete": "✅", "report": "📊"}.get(log['type'], "📝")
        st.markdown(f"<div style='color: #334155; font-weight: 500;'>{icon} {log['action']}</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div style='color: #64748b; font-size: 0.875rem; text-align: right;'>{log['user']}</div>", unsafe_allow_html=True)
    
    if i < len(recent_logs) - 1:
        st.markdown("<div style='border-bottom: 1px solid #E2E8F0; margin: 0.75rem 0;'></div>", unsafe_allow_html=True)

st.markdown("---")

# Call to action buttons with better visual design
st.markdown("## 🚀 Quick Actions")
st.markdown("")

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    if st.button("📥 Generate Report", use_container_width=True, type="primary"):
        with st.spinner("Generating comprehensive compliance report..."):
            import time
            time.sleep(1)
        st.success("✅ Report generated successfully!")
        
with col2:
    if st.button("📧 Send Alerts", use_container_width=True, type="primary"):
        with st.spinner("Sending deadline reminders to team..."):
            import time
            time.sleep(1)
        st.success("✅ Alerts sent to 4 team members!")

with col3:
    if st.button("⚙️ Settings", use_container_width=True, type="primary"):
        st.switch_page("pages/4_⚙️_Settings.py")

# Footer with better styling
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 2rem 0 1rem 0; color: #94A3B8;'>
        <p style='margin: 0; font-size: 0.875rem;'>
            <strong style='color: #64748b;'>CompliGH</strong> — Ghana Fintech Compliance Monitor
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.75rem;'>
            Powered by Streamlit • Built with ❤️ for Ghana's fintech ecosystem
        </p>
    </div>
""", unsafe_allow_html=True)
