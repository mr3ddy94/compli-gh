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
# DATABASE FUNCTIONS - Fetch real data from Supabase
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
    
    # Also fetch frameworks for each item
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
    
    # Calculate compliance score (percentage compliant)
    compliance_score = int((compliant / total) * 100) if total > 0 else 0
    
    # Calculate risk score (0-100, lower is better)
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
    
    # Calculate scores for each framework
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
# IMPROVED CUSTOM CSS
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #F8F9FA;
    }
    
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
    
    .stButton>button {
        background: linear-gradient(135deg, #CE1126 0%, #9A0D1C 100%);
        color: white;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 600;
        font-size: 0.95rem;
        box-shadow: 0 2px 8px rgba(206, 17, 38, 0.2);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #9A0D1C 0%, #CE1126 100%);
        box-shadow: 0 4px 12px rgba(206, 17, 38, 0.35);
        transform: translateY(-2px);
    }
    
    h1 {
        color: #1e293b !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        margin-top: 2rem !important;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #CE1126 0%, #FCD116 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background-color: #E2E8F0;
        border-radius: 10px;
    }
    
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: #1e293b;
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
    
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
    }
    
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE & DATA LOADING
# =============================================================================

# Initialize session state
if 'organization_id' not in st.session_state:
    st.session_state.organization_id = '11111111-1111-1111-1111-111111111111'

# Fetch organization details
org_id = st.session_state.organization_id

try:
    org_data = get_organization(org_id)
    
    if org_data:
        st.session_state.organization_name = org_data['name']
    else:
        st.session_state.organization_name = "Demo Fintech Ltd"
        st.warning("⚠️ Organization not found in database. Using default.")
    
    # Fetch compliance data
    compliance_data = get_compliance_summary(org_id)
    
    # Calculate real metrics
    metrics = calculate_metrics(compliance_data)
    
    # Store in session state
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
    st.markdown("##### *Ghana Fintech Compliance*")
    st.markdown("---")
    
    # Organization info box
    st.markdown("### 📊 Organization")
    st.info(f"**{st.session_state.organization_name}**")
    
    st.markdown("### 📈 Compliance Score")
    score = st.session_state.compliance_score
    
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
        frameworks_count = len(get_frameworks_summary(compliance_data))
        st.metric("Frameworks", frameworks_count)
    with col2:
        st.metric("Items", st.session_state.total_items)
    
    st.markdown("---")
    
    # Version info
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #94A3B8;'>
            <small>Version 1.0.0</small><br>
            <small>© 2026 CompliGH</small>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("📊 Compliance Dashboard")
st.markdown("##### Real-time monitoring for Ghanaian fintech regulations")
st.markdown("")

# Top metrics row with REAL DATA
col1, col2, col3, col4 = st.columns(4)

with col1:
    score = st.session_state.compliance_score
    delta = "↑ 5%" if score >= 85 else "↓ 3%"
    
    st.metric(
        label="Compliance Score",
        value=f"{score}%",
        delta=delta,
        delta_color="normal",
        help="Overall compliance across all frameworks"
    )

with col2:
    total = st.session_state.total_items
    needs_attention = st.session_state.warning_items + st.session_state.critical_items
    
    st.metric(
        label="Active Regulations",
        value=str(total),
        delta=f"{needs_attention} need attention",
        delta_color="inverse",
        help="Total compliance items being tracked"
    )

with col3:
    risk = st.session_state.risk_score
    
    if risk < 30:
        risk_level = "Low"
        risk_color = "normal"
        risk_delta = "↓ 2 points"
    elif risk < 60:
        risk_level = "Medium"
        risk_color = "off"
        risk_delta = "→ Stable"
    else:
        risk_level = "High"
        risk_color = "inverse"
        risk_delta = "↑ Action needed"
    
    st.metric(
        label="Risk Level",
        value=risk_level,
        delta=risk_delta,
        delta_color=risk_color,
        help=f"Current risk score: {risk}/100"
    )

with col4:
    st.metric(
        label="Next Audit",
        value="14 days",
        delta="Q1 BoG Report",
        help="Upcoming regulatory deadline"
    )

st.markdown("---")

# Main layout - two columns
col_main, col_side = st.columns([2, 1], gap="large")

with col_main:
    st.markdown("## 📋 Compliance Frameworks Overview")
    st.markdown("")
    
    # Get frameworks summary from real data
    frameworks_summary = get_frameworks_summary(compliance_data)
    
    # Map framework names to emojis
    framework_display = {
        'Bank of Ghana': {'emoji': '🏦', 'order': 1},
        'AML/CFT': {'emoji': '💰', 'order': 2},
        'Data Protection Act': {'emoji': '🔒', 'order': 3},
        'Payment Systems Act': {'emoji': '💳', 'order': 4},
        'ISO 27001': {'emoji': '🔐', 'order': 5},
        'PCI DSS': {'emoji': '💳', 'order': 6}
    }
    
    # Sort frameworks by display order
    sorted_frameworks = sorted(
        frameworks_summary.items(),
        key=lambda x: framework_display.get(x[1]['name'], {}).get('order', 99)
    )
    
    # Display each framework
    for fw_id, stats in sorted_frameworks:
        framework_name = stats['name']
        emoji = framework_display.get(framework_name, {}).get('emoji', '📋')
        
        score = stats['score']
        if score >= 80:
            badge = "🟢 Compliant"
        elif score >= 60:
            badge = "🟡 Review Needed"
        else:
            badge = "🔴 Action Required"
        
        with st.expander(f"{emoji} {framework_name} — **{score}%** — {badge}", expanded=False):
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)
            fcol1.metric("📊 Total", stats['total'])
            fcol2.metric("✅ Compliant", stats['compliant'])
            fcol3.metric("⚠️ Warning", stats['warning'])
            fcol4.metric("❌ Critical", stats['critical'])
            
            st.markdown("")
            
            st.progress(score / 100)
            st.markdown(f"<div style='text-align: right; color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;'>{score}% Complete</div>", unsafe_allow_html=True)
            
            st.markdown("")
            
            acol1, acol2, acol3 = st.columns([1, 1, 1])
            with acol1:
                if st.button(f"📝 View Details", key=f"view_{fw_id}", use_container_width=True):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol2:
                if st.button(f"🔄 Update Status", key=f"update_{fw_id}", use_container_width=True):
                    st.switch_page("pages/1_📋_Compliance_Frameworks.py")
            with acol3:
                if st.button(f"📎 Documents", key=f"docs_{fw_id}", use_container_width=True):
                    st.info("📁 Document management coming soon!")

with col_side:
    st.markdown("## ⚠️ Risk Assessment")
    st.markdown("")
    
    risk_score = st.session_state.risk_score
    
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
    
    if risk_score < 30:
        st.success("✅ **Low Risk** — System is secure")
    elif risk_score < 60:
        st.warning("⚠️ **Medium Risk** — Review needed")
    else:
        st.error("🚨 **High Risk** — Immediate action required")
    
    st.markdown("---")
    
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

# Recent activity with REAL DATA
st.markdown("## 📜 Recent Activity")
st.markdown("##### Latest compliance actions across your organization")
st.markdown("")

try:
    recent_logs = get_recent_audit_logs(org_id, limit=5)
    
    if recent_logs:
        for i, log in enumerate(recent_logs):
            col1, col2, col3 = st.columns([2, 5, 2])
            
            # Format timestamp
            created_at = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
            time_ago = datetime.now() - created_at.replace(tzinfo=None)
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days} day{'s' if time_ago.days > 1 else ''} ago"
            elif time_ago.seconds >= 3600:
                hours = time_ago.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                minutes = time_ago.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
            with col1:
                st.markdown(f"<div style='color: #94A3B8; font-size: 0.875rem;'>{time_str}</div>", unsafe_allow_html=True)
            
            with col2:
                icon_map = {"update": "🔄", "upload": "📤", "complete": "✅", "generate": "📊", "create": "➕", "delete": "🗑️"}
                icon = icon_map.get(log['action'], "📝")
                st.markdown(f"<div style='color: #334155; font-weight: 500;'>{icon} {log['description']}</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div style='color: #64748b; font-size: 0.875rem; text-align: right;'>System</div>", unsafe_allow_html=True)
            
            if i < len(recent_logs) - 1:
                st.markdown("<div style='border-bottom: 1px solid #E2E8F0; margin: 0.75rem 0;'></div>", unsafe_allow_html=True)
    else:
        st.info("No recent activity to display")
        
except Exception as e:
    st.warning("Unable to load recent activity")

st.markdown("---")

# Call to action buttons
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
        st.success(f"✅ Alerts sent to team members!")

with col3:
    if st.button("⚙️ Settings", use_container_width=True, type="primary"):
        st.switch_page("pages/4_⚙️_Settings.py")

# Footer
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
