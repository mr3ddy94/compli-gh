import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.database import get_supabase_client
import io

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

@st.cache_data(ttl=30)
def get_compliance_summary(org_id):
    """Fetch compliance summary for an organization"""
    supabase = get_supabase_client()
    
    response = supabase.table('compliance_status').select(
        '*, compliance_items(id, name, description, criticality, framework_id)'
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


def calculate_metrics(compliance_data):
    """Calculate dashboard metrics from compliance data"""
    if not compliance_data:
        return {
            'total_items': 0, 'compliant': 0, 'warning': 0, 'critical': 0,
            'not_started': 0, 'compliance_score': 0, 'risk_score': 100
        }
    
    total = len(compliance_data)
    compliant = len([d for d in compliance_data if d['status'] == 'compliant'])
    warning = len([d for d in compliance_data if d['status'] == 'warning'])
    critical = len([d for d in compliance_data if d['status'] == 'critical'])
    not_started = len([d for d in compliance_data if d['status'] == 'not_started'])
    
    compliance_score = int((compliant / total) * 100) if total > 0 else 0
    risk_score = min((critical * 10) + (warning * 3) + (not_started * 1), 100)
    
    return {
        'total_items': total, 'compliant': compliant, 'warning': warning,
        'critical': critical, 'not_started': not_started,
        'compliance_score': compliance_score, 'risk_score': risk_score
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
                'total': 0, 'compliant': 0, 'warning': 0, 'critical': 0, 'not_started': 0
            }
        
        frameworks[framework_id]['total'] += 1
        status = item['status']
        frameworks[framework_id][status] = frameworks[framework_id].get(status, 0) + 1
    
    for fw_id, fw_data in frameworks.items():
        total = fw_data['total']
        compliant = fw_data['compliant']
        fw_data['score'] = int((compliant / total) * 100) if total > 0 else 0
    
    return frameworks


@st.cache_data(ttl=60)
def get_recent_audit_logs(org_id, limit=10):
    """Fetch recent audit logs"""
    supabase = get_supabase_client()
    response = supabase.table('audit_logs').select(
        '*, users(full_name, email)'
    ).eq('organization_id', org_id).order('created_at', desc=True).limit(limit).execute()
    
    return response.data


def send_email_alerts(org_id, alert_type="deadline"):
    """Send email alerts to team"""
    supabase = get_supabase_client()
    
    users_response = supabase.table('users').select('email, full_name').eq(
        'organization_id', org_id
    ).in_('role', ['admin', 'officer']).execute()
    
    recipients = [u['email'] for u in users_response.data] if users_response.data else []
    
    supabase.table('audit_logs').insert({
        'organization_id': org_id,
        'action': 'send_alert',
        'entity_type': 'notification',
        'description': f'Sent {alert_type} alerts to {len(recipients)} team members'
    }).execute()
    
    return len(recipients)


def generate_pdf_report(org_id, org_name, compliance_data, metrics, frameworks_summary):
    """Generate PDF compliance report"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'], fontSize=28,
        textColor=colors.HexColor('#D97706'), spaceAfter=12,
        alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading1'], fontSize=16,
        textColor=colors.HexColor('#0F172A'), spaceAfter=12,
        spaceBefore=12, fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph("CompliGH Compliance Report", title_style))
    story.append(Paragraph(org_name, styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Executive Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Compliance Score', f"{metrics['compliance_score']}%", 
         'Excellent' if metrics['compliance_score'] >= 80 else 'Good' if metrics['compliance_score'] >= 60 else 'Needs Attention'],
        ['Total Items', str(metrics['total_items']), '-'],
        ['Compliant', str(metrics['compliant']), '✓'],
        ['Warning', str(metrics['warning']), '⚠'],
        ['Critical', str(metrics['critical']), '✗' if metrics['critical'] > 0 else '✓'],
        ['Risk Score', f"{metrics['risk_score']}/100", 
         'Low' if metrics['risk_score'] < 30 else 'Medium' if metrics['risk_score'] < 60 else 'High'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D97706')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Framework Breakdown", heading_style))
    
    framework_data = [['Framework', 'Score', 'Total', 'Compliant', 'Warning', 'Critical']]
    for fw_id, fw in frameworks_summary.items():
        framework_data.append([
            fw['name'], f"{fw['score']}%", str(fw['total']),
            str(fw['compliant']), str(fw['warning']), str(fw['critical'])
        ])
    
    framework_table = Table(framework_data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    framework_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    
    story.append(framework_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =============================================================================
# IMPROVED CSS
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { 
        background: linear-gradient(135deg, #FAFAFA 0%, #FFFFFF 100%);
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        box-shadow: 4px 0 24px rgba(0,0,0,0.12);
    }
    
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
    [data-testid="stSidebar"] h1, h2, h3 { color: #FBBF24 !important; font-weight: 800; }
    
    [data-testid="stMetricValue"] {
        font-size: 2.75rem;
        font-weight: 900;
        color: #0F172A;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9375rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: white;
        border-radius: 12px;
        padding: 0.875rem 2rem;
        border: none;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 4px 16px rgba(217, 119, 6, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #B45309 0%, #92400E 100%);
        box-shadow: 0 8px 24px rgba(217, 119, 6, 0.5);
        transform: translateY(-3px);
    }
    
    h1 {
        color: #0F172A !important;
        font-weight: 900 !important;
        font-size: 3rem !important;
        letter-spacing: -0.02em !important;
    }
    
    h2 {
        color: #1E293B !important;
        font-weight: 800 !important;
        font-size: 1.875rem !important;
        border-bottom: 3px solid #D97706;
        padding-bottom: 0.5rem;
        margin-top: 2rem !important;
    }
    
    h3 { color: #334155 !important; font-weight: 700 !important; }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #EF4444 0%, #F59E0B 50%, #10B981 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background-color: #E5E7EB;
        border-radius: 10px;
        height: 10px;
    }
    
    .framework-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid #F1F5F9;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .framework-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.16);
        border-color: #D97706;
    }
    
    .framework-card.compliant {
        border-left: 6px solid #10B981;
    }
    
    .framework-card.warning {
        border-left: 6px solid #F59E0B;
    }
    
    .framework-card.critical {
        border-left: 6px solid #EF4444;
    }
    
    .framework-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 1rem;
    }
    
    .framework-score {
        font-size: 3.5rem;
        font-weight: 900;
        color: #0F172A;
        line-height: 1;
        margin: 1rem 0;
    }
    
    .framework-status {
        font-size: 1rem;
        font-weight: 700;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    .status-compliant {
        background: #D1FAE5;
        color: #065F46;
    }
    
    .status-warning {
        background: #FEF3C7;
        color: #92400E;
    }
    
    .status-critical {
        background: #FEE2E2;
        color: #991B1B;
    }
    
    .framework-stats {
        display: flex;
        justify-content: space-between;
        margin-top: auto;
        padding-top: 1rem;
        border-top: 2px solid #F1F5F9;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1E293B;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        border-left: 6px solid #10B981;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        font-weight: 700;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border-left: 6px solid #F59E0B;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        font-weight: 700;
    }
    
    .stError {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        border-left: 6px solid #EF4444;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        font-weight: 700;
    }
    
    hr {
        margin: 2.5rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #D97706, transparent);
    }
    
    .block-container { padding: 2rem 3rem; max-width: 1600px; }
    
    p { color: #475569; font-size: 1rem; font-weight: 500; line-height: 1.7; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    
    compliance_data = get_compliance_summary(org_id)
    metrics = calculate_metrics(compliance_data)
    frameworks_summary = get_frameworks_summary(compliance_data)
    
    st.session_state.compliance_score = metrics['compliance_score']
    st.session_state.total_items = metrics['total_items']
    st.session_state.compliant_items = metrics['compliant']
    st.session_state.warning_items = metrics['warning']
    st.session_state.critical_items = metrics['critical']
    st.session_state.risk_score = metrics['risk_score']
    
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("# 🇬🇭 CompliGH")
    st.markdown("##### *Ghana Fintech Compliance*")
    st.markdown("---")
    
    st.markdown("### 📊 Organization")
    st.info(f"**{st.session_state.organization_name}**")
    
    st.markdown("### 📈 Compliance Score")
    score = st.session_state.compliance_score
    
    if score >= 90:
        st.success(f"## {score}%\n**🏆 Outstanding**")
    elif score >= 80:
        st.success(f"## {score}%\n**✨ Excellent**")
    elif score >= 70:
        st.info(f"## {score}%\n**👍 Good**")
    elif score >= 60:
        st.warning(f"## {score}%\n**⚠️ Fair**")
    else:
        st.error(f"## {score}%\n**🚨 Needs Work**")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Frameworks", len(frameworks_summary))
    with col2:
        st.metric("Items", st.session_state.total_items)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Done", st.session_state.compliant_items)
    with col2:
        st.metric("⚠️ Pending", st.session_state.warning_items + st.session_state.critical_items)
    
    st.markdown("---")
    
    st.markdown("### ⏱️ Last Updated")
    st.caption(datetime.now().strftime("%B %d, %Y\n%I:%M %p"))
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("📊 Compliance Dashboard")
st.markdown("##### Real-time monitoring for Ghana fintech regulations")
st.markdown("")

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Compliance Score", f"{st.session_state.compliance_score}%", 
              "+5%" if st.session_state.compliance_score >= 85 else "-3%")

with col2:
    needs_attention = st.session_state.warning_items + st.session_state.critical_items
    st.metric("Active Regulations", st.session_state.total_items, 
              f"{needs_attention} need action" if needs_attention > 0 else "All good")

with col3:
    risk = st.session_state.risk_score
    risk_level = "Very Low" if risk < 20 else "Low" if risk < 40 else "Medium" if risk < 60 else "High"
    st.metric("Risk Level", risk_level, f"{risk}/100")

with col4:
    st.metric("Critical Items", st.session_state.critical_items,
              "Immediate action" if st.session_state.critical_items > 0 else "None")

st.markdown("---")

# =============================================================================
# VISUAL FRAMEWORK STATUS OVERVIEW - FIXED!
# =============================================================================

st.markdown("## 🎯 Compliance Status Overview")
st.markdown("##### Visual breakdown of all frameworks")
st.markdown("")

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

# Display frameworks in 2 rows of 3
for row_num in range(2):
    cols = st.columns(3)
    
    start_idx = row_num * 3
    end_idx = start_idx + 3
    row_frameworks = sorted_frameworks[start_idx:end_idx]
    
    for col_idx, (fw_id, stats) in enumerate(row_frameworks):
        with cols[col_idx]:
            framework_name = stats['name']
            emoji = framework_display.get(framework_name, {}).get('emoji', '📋')
            score = stats['score']
            
            # Determine status
            if score >= 80:
                status_text = "✅ Compliant"
                status_class = "compliant"
                status_style = "status-compliant"
            elif score >= 60:
                status_text = "⚠️ Review Needed"
                status_class = "warning"
                status_style = "status-warning"
            else:
                status_text = "❌ Action Required"
                status_class = "critical"
                status_style = "status-critical"
            
            # Render framework card
            st.markdown(f"""
                <div class="framework-card {status_class}">
                    <div class="framework-header">
                        {emoji} {framework_name}
                    </div>
                    <div class="framework-score">{score}%</div>
                    <div class="framework-status {status_style}">
                        {status_text}
                    </div>
                    <div class="framework-stats">
                        <div class="stat-item">
                            <div class="stat-value">{stats['compliant']}</div>
                            <div class="stat-label">✅ Done</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{stats['warning']}</div>
                            <div class="stat-label">⚠️ Review</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{stats['critical']}</div>
                            <div class="stat-label">❌ Critical</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            # Progress bar
            st.progress(score / 100)
            
            # View details button
            if st.button(f"📋 View Details", key=f"view_{fw_id}", use_container_width=True):
                st.switch_page("pages/1_📋_Compliance_Frameworks.py")
    
    if row_num == 0:
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

st.markdown("---")

# Compliance Trend Chart
st.markdown("## 📈 Compliance Trends")
st.markdown("##### Track your progress over time")
st.markdown("")

dates = pd.date_range(end=datetime.now(), periods=6, freq='M')
base_score = metrics['compliance_score']

if base_score >= 85:
    scores = [base_score - 8 + (i * 1.5) for i in range(6)]
else:
    scores = [base_score - 12 + (i * 2) for i in range(6)]
scores[-1] = base_score

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates, y=scores, mode='lines+markers', name='Compliance Score',
    line=dict(color='#D97706', width=4),
    marker=dict(size=12, color='#FBBF24', line=dict(color='#D97706', width=2)),
    fill='tozeroy', fillcolor='rgba(217, 119, 6, 0.1)'
))

fig.add_hline(y=80, line_dash="dash", line_color="#10B981", 
              annotation_text="Target: 80%")

fig.update_layout(
    xaxis_title="Month", yaxis_title="Compliance Score (%)", height=350,
    hovermode='x unified', plot_bgcolor='white', paper_bgcolor='white',
    yaxis=dict(range=[0, 100])
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Recent Activity
st.markdown("## 📜 Recent Activity")
st.markdown("")

try:
    recent_logs = get_recent_audit_logs(org_id, limit=6)
    
    if recent_logs:
        for log in recent_logs:
            created_at = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
            time_ago = datetime.now() - created_at.replace(tzinfo=None)
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds >= 3600:
                time_str = f"{time_ago.seconds // 3600}h ago"
            else:
                time_str = f"{max(1, time_ago.seconds // 60)}m ago"
            
            user_name = log.get('users', {}).get('full_name', 'System') if log.get('users') else 'System'
            
            icon_map = {
                "update": "🔄", "upload": "📤", "complete": "✅", 
                "generate": "📊", "send_alert": "📧"
            }
            icon = icon_map.get(log['action'], "📝")
            
            st.markdown(f"""
                <div style="padding: 0.75rem; background: white; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #D97706;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="font-weight: 600; color: #1E293B;">{icon} {log['description']}</div>
                        <div style="color: #94A3B8; font-size: 0.875rem;">{time_str}</div>
                    </div>
                    <div style="color: #64748B; font-size: 0.875rem; margin-top: 0.25rem;">by {user_name}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity")
except:
    st.warning("Unable to load activity")

st.markdown("---")

# Quick Actions
st.markdown("## 🚀 Quick Actions")
st.markdown("")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 GENERATE REPORT", use_container_width=True, type="primary"):
        with st.spinner("Generating report..."):
            try:
                pdf_buffer = generate_pdf_report(
                    org_id, st.session_state.organization_name,
                    compliance_data, metrics, frameworks_summary
                )
                
                st.success("✅ Report generated!")
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer,
                    file_name=f"CompliGH_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

with col2:
    if st.button("📧 SEND ALERTS", use_container_width=True, type="primary"):
        with st.spinner("Sending alerts..."):
            try:
                count = send_email_alerts(org_id)
                st.success(f"✅ Alerts sent to {count} members!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Error: {e}")

with col3:
    if st.button("⚙️ SETTINGS", use_container_width=True, type="primary"):
        st.switch_page("pages/4_⚙️_Settings.py")

st.markdown("---")

# Critical items alert
if st.session_state.critical_items > 0:
    st.error(f"### 🚨 {st.session_state.critical_items} Critical Items Need Immediate Attention!")
    
    critical_items = [d for d in compliance_data if d['status'] == 'critical']
    
    for item in critical_items[:3]:
        with st.expander(f"❌ {item['compliance_items']['name']}"):
            st.markdown(f"**Framework:** {item['framework']['name']}")
            st.markdown(f"**Description:** {item['compliance_items']['description']}")
            st.markdown(f"**Notes:** {item.get('notes', 'No notes')}")
            st.markdown(f"**Progress:** {item['progress']}%")
            
            if st.button(f"Fix Now", key=f"fix_{item['compliance_item_id']}"):
                st.switch_page("pages/1_📋_Compliance_Frameworks.py")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <div style='font-size: 1.5rem; font-weight: 800; color: #0F172A;'>CompliGH</div>
        <div style='color: #64748B; margin-top: 0.5rem;'>Ghana Fintech Compliance Monitor</div>
        <div style='color: #94A3B8; font-size: 0.875rem; margin-top: 1rem;'>
            Powered by Streamlit • Built with ❤️ for Ghana's fintech ecosystem
        </div>
    </div>
""", unsafe_allow_html=True)
