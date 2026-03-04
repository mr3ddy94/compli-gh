import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="CompliGH - Ghana Fintech Compliance",
    page_icon="🇬🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Ghana colors theme
st.markdown("""
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1A1F2E;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #CE1126;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #9A0D1C;
        border: none;
    }
    
    /* Headers */
    h1 {
        color: #CE1126;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #CE1126;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'organization_name' not in st.session_state:
    st.session_state.organization_name = "Demo Fintech Ltd"
if 'compliance_score' not in st.session_state:
    st.session_state.compliance_score = 87

# Sidebar
with st.sidebar:
    st.title("🇬🇭 CompliGH")
    st.markdown("---")
    
    # Organization info
    st.markdown("### 📊 Organization")
    st.info(st.session_state.organization_name)
    
    st.markdown("### 📈 Compliance Score")
    score = st.session_state.compliance_score
    if score >= 80:
        st.success(f"{score}%")
    elif score >= 60:
        st.warning(f"{score}%")
    else:
        st.error(f"{score}%")
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### 🎯 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Frameworks", "6")
    with col2:
        st.metric("Items", "36")
    
    st.markdown("---")
    st.caption("Version 1.0.0")
    st.caption("© 2026 CompliGH")

# Main content
st.title("📊 Compliance Dashboard")
st.markdown("Real-time monitoring for Ghanaian fintech regulations")

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Compliance Score",
        value="87%",
        delta="↑ 5%",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Active Regulations",
        value="36",
        delta="8 need attention",
        delta_color="inverse"
    )

with col3:
    st.metric(
        label="Risk Level",
        value="Low",
        delta="↓ 2 points",
        delta_color="normal"
    )

with col4:
    st.metric(
        label="Next Audit",
        value="14 days",
        delta="Q1 BoG Report"
    )

st.markdown("---")

# Main layout - two columns
col_main, col_side = st.columns([2, 1])

with col_main:
    st.subheader("📋 Compliance Frameworks Overview")
    
    # Framework summary
    frameworks = {
        "Bank of Ghana": {"total": 22, "compliant": 18, "warning": 3, "critical": 1, "score": 82},
        "AML/CFT": {"total": 13, "compliant": 10, "warning": 2, "critical": 1, "score": 77},
        "Data Protection Act": {"total": 9, "compliant": 8, "warning": 1, "critical": 0, "score": 89},
        "Payment Systems Act": {"total": 8, "compliant": 7, "warning": 1, "critical": 0, "score": 88},
        "ISO 27001": {"total": 8, "compliant": 5, "warning": 2, "critical": 1, "score": 63},
        "PCI DSS": {"total": 6, "compliant": 5, "warning": 1, "critical": 0, "score": 83}
    }
    
    for framework, stats in frameworks.items():
        with st.expander(f"**{framework}** - {stats['score']}% compliant", expanded=False):
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)
            fcol1.metric("Total", stats['total'])
            fcol2.metric("✓ Compliant", stats['compliant'])
            fcol3.metric("⚠ Warning", stats['warning'])
            fcol4.metric("❌ Critical", stats['critical'])
            
            # Progress bar
            st.progress(stats['score'] / 100)
            
            # Quick actions
            acol1, acol2 = st.columns(2)
            with acol1:
                if st.button(f"View Details", key=f"view_{framework}"):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol2:
                if st.button(f"Update Status", key=f"update_{framework}"):
                    st.info("Status update feature coming soon!")

with col_side:
    # Risk gauge
    st.subheader("⚠️ Risk Assessment")
    
    risk_score = 32
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#CE1126"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': '#10B981'},
                {'range': [30, 60], 'color': '#F59E0B'},
                {'range': [60, 100], 'color': '#DC2626'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk level badge
    if risk_score < 30:
        st.success("✓ Low Risk")
    elif risk_score < 60:
        st.warning("⚠ Medium Risk")
    else:
        st.error("❌ High Risk")
    
    st.markdown("---")
    
    # Upcoming deadlines
    st.subheader("📅 Upcoming Deadlines")
    
    deadlines = [
        {"task": "Quarterly BoG Report", "days": 14, "status": "warning"},
        {"task": "AML Risk Assessment", "days": 28, "status": "info"},
        {"task": "DPC Annual Filing", "days": 45, "status": "info"},
        {"task": "ISO 27001 Audit", "days": 60, "status": "info"}
    ]
    
    for deadline in deadlines:
        if deadline['status'] == 'warning':
            st.warning(f"⏰ **{deadline['task']}**\n\n{deadline['days']} days")
        else:
            st.info(f"📌 **{deadline['task']}**\n\n{deadline['days']} days")

st.markdown("---")

# Recent activity
st.subheader("📜 Recent Activity")

recent_logs = [
    {"time": "2 hours ago", "action": "Updated CDD status", "user": "John Mensah"},
    {"time": "5 hours ago", "action": "Uploaded AML policy document", "user": "Ama Kwakye"},
    {"time": "Yesterday", "action": "Completed ISO 27001 training", "user": "Kofi Asante"},
    {"time": "2 days ago", "action": "Generated compliance report", "user": "John Mensah"}
]

for log in recent_logs:
    col1, col2, col3 = st.columns([2, 4, 2])
    with col1:
        st.caption(log['time'])
    with col2:
        st.text(log['action'])
    with col3:
        st.caption(f"by {log['user']}")

st.markdown("---")

# Call to action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Generate Report", use_container_width=True):
        st.success("Generating comprehensive compliance report...")
        
with col2:
    if st.button("📧 Send Alerts", use_container_width=True):
        st.info("Sending deadline reminders to team...")

with col3:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/4_⚙️_Settings.py")

# Footer
st.markdown("---")
st.caption("CompliGH - Ghana Fintech Compliance Monitor | Powered by Streamlit")
