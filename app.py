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

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

@st.cache_data(ttl=60)
def get_compliance_summary(org_id):
    """Fetch compliance summary for an organization"""
    supabase = get_supabase_client()
    
    response = supabase.table('compliance_status').select(
        '''
        *,
        compliance_items(
            id,
            name,
            description,
            criticality,
            framework_id
        )
        '''
    ).eq('organization_id', org_id).execute()
    
    enhanced_data = []
    for item in response.data:
        framework_response = supabase.table('frameworks').select('*').eq(
            'id', item['compliance_items']['framework_id']
        ).execute()
        
        item['framework'] = framework_response.data[0] if framework_response.data else None
        enhanced_data.append(item)
    
    return enhanced_data


@st.cache_data(ttl=300)
def get_organization(org_id):
    """Fetch organization details"""
    supabase = get_supabase_client()
    response = supabase.table('organizations').select('*').eq('id', org_id).execute()
    return response.data[0] if response.data else None


@st.cache_data(ttl=60)
def calculate_metrics(compliance_data):
    """Calculate dashboard metrics from compliance data"""
    if not compliance_data:
        return {
            'total_items': 0,
            'compliant': 0,
            'warning': 0,
            'critical': 0,
            'not_started': 0,
            'compliance_score': 0,
            'risk_score': 100
        }
    
    total = len(compliance_data)
    compliant = len([d for d in compliance_data if d['status'] == 'compliant'])
    warning = len([d for d in compliance_data if d['status'] == 'warning'])
    critical = len([d for d in compliance_data if d['status'] == 'critical'])
    not_started = len([d for d in compliance_data if d['status'] == 'not_started'])
    
    compliance_score = int((compliant / total) * 100) if total > 0 else 0
    
    risk_score = 0
    if total > 0:
        risk_score = (
            (critical * 10) +
            (warning * 3) +
            (not_started * 1)
        )
        risk_score = min(risk_score, 100)
    
    return {
        'total_items': total,
        'compliant': compliant,
        'warning': warning,
        'critical': critical,
        'not_started': not_started,
        'compliance_score': compliance_score,
        'risk_score': risk_score
    }


def get_frameworks_summary(compliance_data):
    """Group compliance data by framework"""
    frameworks = {}
    
    for item in compliance_data:
        if not item.get('framework'):
            continue
            
        framework_name = item['framework']['name']
        framework_id = item['framework']['id']
        
        if framework_id not in frameworks:
            frameworks[framework_id] = {
                'name': framework_name,
                'short_code': item['framework']['short_code'],
                'total': 0,
                'compliant': 0,
                'warning': 0,
                'critical': 0,
                'not_started': 0
            }
        
        frameworks[framework_id]['total'] += 1
        
        status = item['status']
        if status == 'compliant':
            frameworks[framework_id]['compliant'] += 1
        elif status == 'warning':
            frameworks[framework_id]['warning'] += 1
        elif status == 'critical':
            frameworks[framework_id]['critical'] += 1
        else:
            frameworks[framework_id]['not_started'] += 1
    
    for fw_id, fw_data in frameworks.items():
        total = fw_data['total']
        compliant = fw_data['compliant']
        fw_data['score'] = int((compliant / total) * 100) if total > 0 else 0
    
    return frameworks


@st.cache_data(ttl=60)
def get_recent_audit_logs(org_id, limit=5):
    """Fetch recent audit logs"""
    supabase = get_supabase_client()
    response = supabase.table('audit_logs').select('*').eq(
        'organization_id', org_id
    ).order('created_at', desc=True).limit(limit).execute()
    
    return response.data


# =============================================================================
# IMPROVED CUSTOM CSS - Better Contrast & Complementary Colors
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background - Clean white */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Sidebar - Deep navy with gold accents */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        padding: 2rem 1rem;
        border-right: 3px solid #D97706;
    }
    
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #FBBF24 !important;
        font-weight: 800 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #FDE68A !important;
        font-weight: 700 !important;
    }
    
    /* Metric cards - High contrast */
    [data-testid="stMetricValue"] {
        font-size: 3rem;
        font-weight: 800;
        color: #0F172A;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Buttons - Bold orange/amber scheme */
    .stButton>button {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: #FFFFFF;
        border-radius: 12px;
        padding: 1rem 2rem;
        border: none;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.03em;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #B45309 0%, #92400E 100%);
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.5);
        transform: translateY(-3px);
    }
    
    /* Headers - Strong hierarchy */
    h1 {
        color: #0F172A !important;
        font-weight: 900 !important;
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.03em !important;
    }
    
    h2 {
        color: #1E293B !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        border-bottom: 3px solid #D97706;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    /* Progress bars - Amber/orange gradient */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #D97706 0%, #FBBF24 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background-color: #E2E8F0;
        border-radius: 10px;
        height: 12px;
    }
    
    /* Expanders - Clean white cards with strong borders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 3px solid #CBD5E1;
        padding: 1.5rem 2rem;
        font-weight: 700;
        color: #0F172A;
        font-size: 1.125rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #D97706;
        box-shadow: 0 4px 16px rgba(217, 119, 6, 0.2);
        transform: translateY(-2px);
    }
    
    .streamlit-expanderContent {
        background-color: #F8FAFC;
        border: 3px solid #E2E8F0;
        border-top: none;
        border-radius: 0 0 16px 16px;
        padding: 2rem;
    }
    
    /* Success - Strong green */
    .stSuccess {
        background-color: #D1FAE5;
        border-left: 6px solid #059669;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #064E3B;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Warning - Strong amber */
    .stWarning {
        background-color: #FEF3C7;
        border-left: 6px solid #D97706;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #78350F;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Error - Strong red */
    .stError {
        background-color: #FEE2E2;
        border-left: 6px solid #DC2626;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #7F1D1D;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Info - Strong blue */
    .stInfo {
        background-color: #DBEAFE;
        border-left: 6px solid #2563EB;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #1E3A8A;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Metric container cards */
    div[data-testid="column"] > div {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 2px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    
    div[data-testid="column"] > div:hover {
        box-shadow: 0 8px 24px rgba(217, 119, 6, 0.15);
        border-color: #D97706;
        transform: translateY(-4px);
    }
    
    /* Text - Better contrast */
    p, .stMarkdown {
        color: #334155;
        line-height: 1.8;
        font-size: 1.0625rem;
        font-weight: 500;
    }
    
    .stCaption {
        color: #64748B;
        font-size: 0.9375rem;
        font-weight: 500;
    }
    
    /* Horizontal rules */
    hr {
        margin: 3rem 0;
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent, #D97706, transparent);
    }
    
    /* Container spacing */
    .block-container {
        padding: 3rem 4rem;
        max-width: 1600px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #F1F5F9;
        padding: 0.75rem;
        border-radius: 16px;
        border: 2px solid #CBD5E1;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 700;
        color: #475569;
        background-color: transparent;
        border: 2px solid transparent;
        font-size: 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: white;
        border-color: #92400E;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
    }
    
    /* Data frames */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 2px solid #E2E8F0;
    }
    
    /* Links */
    a {
        color: #D97706;
        font-weight: 600;
        text-decoration: none;
    }
    
    a:hover {
        color: #B45309;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE & DATA LOADING
# =============================================================================

if 'organization_id' not in st.session_state:
    st.session_state.organization_id = '11111111-1111-1111-1111-111111111111'

org_id = st.session_state.organization_id

try:
    org_data = get_organization(org_id)
    
    if org_data:
        st.session_state.organization_name = org_data['name']
    else:
        st.session_state.organization_name = "Demo Fintech Ltd"
        st.warning("⚠️ Organization not found in database.")
    
    compliance_data = get_compliance_summary(org_id)
    metrics = calculate_metrics(compliance_data)
    
    st.session_state.compliance_score = metrics['compliance_score']
    st.session_state.total_items = metrics['total_items']
    st.session_state.compliant_items = metrics['compliant']
    st.session_state.warning_items = metrics['warning']
    st.session_state.critical_items = metrics['critical']
    st.session_state.risk_score = metrics['risk_score']
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("💡 Make sure you've set up the database and added seed data in Supabase!")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("# 🇬🇭 CompliGH")
    st.markdown("---")
    
    st.markdown("### 📊 Organization")
    st.info(f"**{st.session_state.organization_name}**")
    
    st.markdown("### 📈 Compliance Score")
    score = st.session_state.compliance_score
    
    if score >= 80:
        st.success(f"# {score}%\n### ✅ Excellent")
    elif score >= 60:
        st.warning(f"# {score}%\n### ⚠️ Good")
    else:
        st.error(f"# {score}%\n### 🔴 Needs Work")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Overview")
    col1, col2 = st.columns(2)
    with col1:
        frameworks_count = len(get_frameworks_summary(compliance_data))
        st.metric("**Frameworks**", frameworks_count)
    with col2:
        st.metric("**Items**", st.session_state.total_items)
    
    st.markdown("---")
    st.caption("**Version** 1.0.0")
    st.caption("© 2026 CompliGH")

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("📊 Compliance Dashboard")
st.markdown("### Real-time compliance monitoring for Ghanaian fintech regulations")
st.markdown("")

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    score = st.session_state.compliance_score
    delta = "↑ 5%" if score >= 85 else "↓ 3%"
    st.metric("Compliance Score", f"{score}%", delta, delta_color="normal")

with col2:
    total = st.session_state.total_items
    needs_attention = st.session_state.warning_items + st.session_state.critical_items
    st.metric("Active Regulations", str(total), f"{needs_attention} need attention", delta_color="inverse")

with col3:
    risk = st.session_state.risk_score
    
    if risk < 30:
        risk_level = "Low"
        risk_delta = "↓ 2 points"
    elif risk < 60:
        risk_level = "Medium"
        risk_delta = "→ Stable"
    else:
        risk_level = "High"
        risk_delta = "↑ Action needed"
    
    st.metric("Risk Level", risk_level, risk_delta)

with col4:
    st.metric("Next Audit", "14 days", "Q1 BoG Report")

st.markdown("---")

# Main layout
col_main, col_side = st.columns([2, 1], gap="large")

with col_main:
    st.markdown("## 📋 Compliance Frameworks")
    st.markdown("")
    
    frameworks_summary = get_frameworks_summary(compliance_data)
    
    framework_display = {
        'Bank of Ghana': {'emoji': '🏦', 'order': 1},
        'AML/CFT': {'emoji': '💰', 'order': 2},
        'Data Protection Act': {'emoji': '🔒', 'order': 3},
        'Payment Systems Act': {'emoji': '💳', 'order': 4},
        'ISO 27001': {'emoji': '🔐', 'order': 5},
        'PCI DSS': {'emoji': '💳', 'order': 6}
    }
    
    sorted_frameworks = sorted(
        frameworks_summary.items(),
        key=lambda x: framework_display.get(x[1]['name'], {}).get('order', 99)
    )
    
    for fw_id, stats in sorted_frameworks:
        framework_name = stats['name']
        emoji = framework_display.get(framework_name, {}).get('emoji', '📋')
        
        score = stats['score']
        if score >= 80:
            badge = "✅ Compliant"
            badge_color = "#059669"
        elif score >= 60:
            badge = "⚠️ Review"
            badge_color = "#D97706"
        else:
            badge = "🔴 Critical"
            badge_color = "#DC2626"
        
        with st.expander(f"{emoji} **{framework_name}** — {score}% — {badge}", expanded=False):
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)
            fcol1.metric("📊 Total", stats['total'])
            fcol2.metric("✅ Compliant", stats['compliant'])
            fcol3.metric("⚠️ Warning", stats['warning'])
            fcol4.metric("🔴 Critical", stats['critical'])
            
            st.markdown("")
            st.progress(score / 100)
            st.markdown(f"**{score}% Complete**")
            st.markdown("")
            
            acol1, acol2, acol3 = st.columns(3)
            with acol1:
                if st.button(f"📝 View Details", key=f"view_{fw_id}", use_container_width=True):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol2:
                if st.button(f"🔄 Update", key=f"update_{fw_id}", use_container_width=True):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol3:
                if st.button(f"📎 Files", key=f"docs_{fw_id}", use_container_width=True):
                    st.info("📁 Coming soon!")

with col_side:
    st.markdown("## ⚠️ Risk Score")
    st.markdown("")
    
    risk_score = st.session_state.risk_score
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Current Risk</b>", 'font': {'size': 20, 'color': '#0F172A'}},
        number={'font': {'size': 56, 'color': '#0F172A', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 3, 'tickcolor': "#94A3B8"},
            'bar': {'color': "#D97706", 'thickness': 0.8},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#CBD5E1",
            'steps': [
                {'range': [0, 30], 'color': '#D1FAE5'},
                {'range': [30, 60], 'color': '#FEF3C7'},
                {'range': [60, 100], 'color': '#FEE2E2'}
            ],
            'threshold': {
                'line': {'color': "#0F172A", 'width': 5},
                'thickness': 0.9,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        font={'color': "#0F172A", 'family': "Inter"},
        height=300,
        margin=dict(l=30, r=30, t=60, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if risk_score < 30:
        st.success("### ✅ Low Risk\nSystem is secure")
    elif risk_score < 60:
        st.warning("### ⚠️ Medium Risk\nReview recommended")
    else:
        st.error("### 🔴 High Risk\nImmediate action needed")
    
    st.markdown("---")
    
    st.markdown("## 📅 Deadlines")
    st.markdown("")
    
    deadlines = [
        {"task": "Quarterly BoG Report", "days": 14, "urgent": True},
        {"task": "AML Risk Assessment", "days": 28, "urgent": False},
        {"task": "DPC Annual Filing", "days": 45, "urgent": False},
        {"task": "ISO 27001 Audit", "days": 60, "urgent": False}
    ]
    
    for deadline in deadlines:
        if deadline['urgent']:
            st.warning(f"**⏰ {deadline['task']}**\n\n{deadline['days']} days remaining")
        else:
            st.info(f"**📋 {deadline['task']}**\n\n{deadline['days']} days")

st.markdown("---")

st.markdown("## 📜 Recent Activity")
st.markdown("")

try:
    recent_logs = get_recent_audit_logs(org_id, limit=5)
    
    if recent_logs:
        for log in recent_logs:
            col1, col2 = st.columns([1, 5])
            
            created_at = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
            time_ago = datetime.now() - created_at.replace(tzinfo=None)
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds >= 3600:
                hours = time_ago.seconds // 3600
                time_str = f"{hours}h ago"
            else:
                minutes = max(1, time_ago.seconds // 60)
                time_str = f"{minutes}m ago"
            
            with col1:
                st.markdown(f"**{time_str}**")
            
            with col2:
                icon_map = {"update": "🔄", "upload": "📤", "complete": "✅", "generate": "📊"}
                icon = icon_map.get(log['action'], "📝")
                st.markdown(f"{icon} {log['description']}")
            
            st.markdown("")
    else:
        st.info("No recent activity")
        
except Exception as e:
    st.warning("Unable to load activity")

st.markdown("---")

st.markdown("## 🚀 Quick Actions")
st.markdown("")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 GENERATE REPORT", use_container_width=True):
        st.success("✅ Report generated!")
        
with col2:
    if st.button("📧 SEND ALERTS", use_container_width=True):
        st.success("✅ Alerts sent!")

with col3:
    if st.button("⚙️ SETTINGS", use_container_width=True):
        st.switch_page("pages/4_⚙️_Settings.py")

st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 2rem 0; color: #64748B;'>
        <p style='margin: 0; font-size: 1.125rem; font-weight: 700; color: #334155;'>
            CompliGH — Ghana Fintech Compliance Monitor
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.875rem; font-weight: 500;'>
            Built with ❤️ for Ghana's fintech ecosystem
        </p>
    </div>
""", unsafe_allow_html=True)
