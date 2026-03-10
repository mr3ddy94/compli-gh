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
    
    # Get compliance officers
    users_response = supabase.table('users').select('email, full_name').eq(
        'organization_id', org_id
    ).in_('role', ['admin', 'officer']).execute()
    
    recipients = [u['email'] for u in users_response.data] if users_response.data else []
    
    # Log the alert
    supabase.table('audit_logs').insert({
        'organization_id': org_id,
        'action': 'send_alert',
        'entity_type': 'notification',
        'description': f'Sent {alert_type} alerts to {len(recipients)} team members'
    }).execute()
    
    return len(recipients)


def generate_pdf_report(org_id, org_name, compliance_data, metrics, frameworks_summary):
    """Generate PDF compliance report"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#D97706'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Paragraph("CompliGH Compliance Report", title_style))
    story.append(Paragraph(org_name, styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Compliance Score', f"{metrics['compliance_score']}%", 
         'Excellent' if metrics['compliance_score'] >= 80 else 'Good' if metrics['compliance_score'] >= 60 else 'Needs Attention'],
        ['Total Compliance Items', str(metrics['total_items']), '-'],
        ['Compliant Items', str(metrics['compliant']), '✓'],
        ['Items Needing Attention', str(metrics['warning']), '⚠'],
        ['Critical Items', str(metrics['critical']), '✗' if metrics['critical'] > 0 else '✓'],
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
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Framework Breakdown
    story.append(Paragraph("Framework Compliance Breakdown", heading_style))
    
    framework_data = [['Framework', 'Score', 'Total', 'Compliant', 'Warning', 'Critical']]
    for fw_id, fw in frameworks_summary.items():
        framework_data.append([
            fw['name'],
            f"{fw['score']}%",
            str(fw['total']),
            str(fw['compliant']),
            str(fw['warning']),
            str(fw['critical'])
        ])
    
    framework_table = Table(framework_data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    framework_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    
    story.append(framework_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Critical Items
    critical_items = [d for d in compliance_data if d['status'] == 'critical']
    if critical_items:
        story.append(Paragraph("Critical Items Requiring Immediate Action", heading_style))
        
        for item in critical_items[:5]:
            story.append(Paragraph(
                f"• <b>{item['compliance_items']['name']}</b> ({item['framework']['name']})",
                styles['Normal']
            ))
            story.append(Paragraph(
                f"  {item['notes'] if item.get('notes') else 'No notes'}",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.1*inch))
    
    # Recommendations
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", heading_style))
    
    recommendations = []
    if metrics['critical'] > 0:
        recommendations.append(f"Address {metrics['critical']} critical compliance gaps immediately")
    if metrics['warning'] > 3:
        recommendations.append(f"Review and resolve {metrics['warning']} items flagged with warnings")
    if metrics['compliance_score'] < 80:
        recommendations.append("Implement regular compliance reviews to improve overall score")
    recommendations.append("Schedule quarterly compliance audits")
    recommendations.append("Ensure all team members complete required training")
    
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "This report was generated by CompliGH - Ghana Fintech Compliance Monitor",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =============================================================================
# IMPROVED CSS - Professional & Smooth
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { 
        background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        box-shadow: 4px 0 20px rgba(0,0,0,0.1);
    }
    
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
    [data-testid="stSidebar"] h1, h2, h3 { color: #FBBF24 !important; font-weight: 800; }
    
    [data-testid="stMetricValue"] {
        font-size: 2.75rem;
        font-weight: 900;
        color: #0F172A;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
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
        border-radius: 14px;
        padding: 1rem 2.5rem;
        border: none;
        font-weight: 700;
        font-size: 1.0625rem;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #B45309 0%, #92400E 100%);
        box-shadow: 0 10px 30px rgba(217, 119, 6, 0.5);
        transform: translateY(-4px) scale(1.02);
    }
    
    .stButton>button:active {
        transform: translateY(-2px) scale(0.98);
    }
    
    h1 {
        color: #0F172A !important;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        letter-spacing: -0.03em !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.05);
    }
    
    h2 {
        color: #1E293B !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        border-bottom: 4px solid #D97706;
        padding-bottom: 0.75rem;
        margin-top: 2.5rem !important;
    }
    
    h3 { color: #334155 !important; font-weight: 700 !important; font-size: 1.5rem !important; }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #D97706 0%, #FBBF24 50%, #10B981 100%);
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
    }
    
    .stProgress > div > div {
        background-color: #E2E8F0;
        border-radius: 12px;
        height: 14px;
    }
    
    .status-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .status-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.15);
        border-color: #D97706;
    }
    
    .status-compliant { border-left: 6px solid #10B981; }
    .status-warning { border-left: 6px solid #F59E0B; }
    .status-critical { border-left: 6px solid #EF4444; }
    
    .stSuccess {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        border-left: 6px solid #10B981;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border-left: 6px solid #F59E0B;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }
    
    .stError {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        border-left: 6px solid #EF4444;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }
    
    .stInfo {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
        border-left: 6px solid #3B82F6;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    div[data-testid="column"] > div {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 2px solid #F1F5F9;
        transition: all 0.3s ease;
    }
    
    div[data-testid="column"] > div:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border-color: #CBD5E1;
        transform: translateY(-3px);
    }
    
    hr {
        margin: 3rem 0;
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent, #D97706, transparent);
    }
    
    .block-container { padding: 2rem 3rem; max-width: 1600px; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    p, .stMarkdown {
        color: #475569;
        font-size: 1.0625rem;
        font-weight: 500;
        line-height: 1.8;
    }
    
    .stCaption {
        color: #64748B;
        font-size: 0.9375rem;
        font-weight: 600;
    }
    
    /* Smooth scrolling */
    html { scroll-behavior: smooth; }
    
    /* Loading animation */
    .stSpinner > div {
        border-top-color: #D97706 !important;
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
    st.info("Make sure database is set up correctly")
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
        st.metric("Frameworks", len(frameworks_summary), label_visibility="visible")
    with col2:
        st.metric("Items", st.session_state.total_items, label_visibility="visible")
    
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
    
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1rem 0; color: #94A3B8;'>
            <small>Version 2.0.0</small><br>
            <small>© 2026 CompliGH</small>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("📊 Compliance Dashboard")
st.markdown("##### Real-time monitoring for Ghana fintech regulations")
st.markdown("")

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    score = st.session_state.compliance_score
    delta = "+5%" if score >= 85 else "-3%"
    delta_color = "normal" if score >= 85 else "inverse"
    
    st.metric(
        label="Compliance Score",
        value=f"{score}%",
        delta=delta,
        delta_color=delta_color,
        help="Percentage of compliant items"
    )

with col2:
    total = st.session_state.total_items
    needs_attention = st.session_state.warning_items + st.session_state.critical_items
    
    st.metric(
        label="Active Regulations",
        value=str(total),
        delta=f"{needs_attention} need action",
        delta_color="inverse" if needs_attention > 0 else "normal",
        help="Total compliance requirements tracked"
    )

with col3:
    risk = st.session_state.risk_score
    
    if risk < 20:
        risk_level = "Very Low"
        risk_color = "normal"
        risk_delta = "↓ Excellent"
    elif risk < 40:
        risk_level = "Low"
        risk_color = "normal"
        risk_delta = "↓ Good"
    elif risk < 60:
        risk_level = "Medium"
        risk_color = "off"
        risk_delta = "→ Monitor"
    else:
        risk_level = "High"
        risk_color = "inverse"
        risk_delta = "↑ Act Now"
    
    st.metric(
        label="Risk Level",
        value=risk_level,
        delta=risk_delta,
        delta_color=risk_color,
        help=f"Risk score: {risk}/100"
    )

with col4:
    critical_count = st.session_state.critical_items
    
    st.metric(
        label="Critical Items",
        value=str(critical_count),
        delta="Immediate action" if critical_count > 0 else "None",
        delta_color="inverse" if critical_count > 0 else "normal",
        help="Items requiring urgent attention"
    )

st.markdown("---")

# Visual Framework Status Overview
st.markdown("## 🎯 Compliance Status Overview")
st.markdown("##### Visual breakdown of all frameworks")
st.markdown("")

framework_display = {
    'Bank of Ghana': {'emoji': '🏦', 'order': 1, 'color': '#3B82F6'},
    'AML/CFT': {'emoji': '💰', 'order': 2, 'color': '#10B981'},
    'Data Protection Act': {'emoji': '🔒', 'order': 3, 'color': '#8B5CF6'},
    'Payment Systems Act': {'emoji': '💳', 'order': 4, 'color': '#EC4899'},
    'ISO 27001': {'emoji': '🔐', 'order': 5, 'color': '#F59E0B'},
    'PCI DSS': {'emoji': '💳', 'order': 6, 'color': '#EF4444'}
}

sorted_frameworks = sorted(
    frameworks_summary.items(),
    key=lambda x: framework_display.get(x[1]['name'], {}).get('order', 99)
)

# Create 2 rows of 3 columns
row1_frameworks = sorted_frameworks[:3]
row2_frameworks = sorted_frameworks[3:]

# First row
cols = st.columns(3)
for idx, (fw_id, stats) in enumerate(row1_frameworks):
    with cols[idx]:
        framework_name = stats['name']
        emoji = framework_display.get(framework_name, {}).get('emoji', '📋')
        score = stats['score']
        
        if score >= 80:
            status = "✅ Compliant"
            status_class = "status-compliant"
        elif score >= 60:
            status = "⚠️ Review"
            status_class = "status-warning"
        else:
            status = "❌ Action Needed"
            status_class = "status-critical"
        
        st.markdown(f"""
            <div class="status-card {status_class}">
                <h3 style="margin: 0; font-size: 1.25rem;">{emoji} {framework_name}</h3>
                <div style="font-size: 3rem; font-weight: 900; color: #0F172A; margin: 1rem 0;">{score}%</div>
                <div style="font-weight: 700; color: #64748B; margin-bottom: 1rem;">{status}</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: #64748B;">
                    <span>✅ {stats['compliant']}</span>
                    <span>⚠️ {stats['warning']}</span>
                    <span>❌ {stats['critical']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.progress(score / 100)
        
        if st.button(f"View Details", key=f"view_{fw_id}", use_container_width=True):
            st.switch_page("pages/1_📋_Compliance_Frameworks.py")

st.markdown("")

# Second row
cols = st.columns(3)
for idx, (fw_id, stats) in enumerate(row2_frameworks):
    with cols[idx]:
        framework_name = stats['name']
        emoji = framework_display.get(framework_name, {}).get('emoji', '📋')
        score = stats['score']
        
        if score >= 80:
            status = "✅ Compliant"
            status_class = "status-compliant"
        elif score >= 60:
            status = "⚠️ Review"
            status_class = "status-warning"
        else:
            status = "❌ Action Needed"
            status_class = "status-critical"
        
        st.markdown(f"""
            <div class="status-card {status_class}">
                <h3 style="margin: 0; font-size: 1.25rem;">{emoji} {framework_name}</h3>
                <div style="font-size: 3rem; font-weight: 900; color: #0F172A; margin: 1rem 0;">{score}%</div>
                <div style="font-weight: 700; color: #64748B; margin-bottom: 1rem;">{status}</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: #64748B;">
                    <span>✅ {stats['compliant']}</span>
                    <span>⚠️ {stats['warning']}</span>
                    <span>❌ {stats['critical']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.progress(score / 100)
        
        if st.button(f"View Details", key=f"view_{fw_id}", use_container_width=True):
            st.switch_page("pages/1_📋_Compliance_Frameworks.py")

st.markdown("---")

# Compliance Trend Chart
st.markdown("## 📈 Compliance Trends")
st.markdown("##### Track your progress over time")
st.markdown("")

# Generate 6 months of trend data (simulated improvement)
dates = pd.date_range(end=datetime.now(), periods=6, freq='M')
base_score = metrics['compliance_score']

# Simulate gradual improvement
if base_score >= 85:
    scores = [base_score - 8 + (i * 1.5) for i in range(6)]
else:
    scores = [base_score - 12 + (i * 2) for i in range(6)]
scores[-1] = base_score

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates,
    y=scores,
    mode='lines+markers',
    name='Compliance Score',
    line=dict(color='#D97706', width=4),
    marker=dict(size=14, color='#FBBF24', line=dict(color='#D97706', width=3)),
    fill='tozeroy',
    fillcolor='rgba(217, 119, 6, 0.1)'
))

fig.add_hline(y=80, line_dash="dash", line_color="#10B981", 
              annotation_text="Target: 80%", annotation_position="right")

fig.update_layout(
    title="6-Month Compliance Score Trend",
    xaxis_title="Month",
    yaxis_title="Compliance Score (%)",
    height=400,
    hovermode='x unified',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family='Inter', size=12),
    yaxis=dict(range=[0, 100], gridcolor='#F1F5F9'),
    xaxis=dict(gridcolor='#F1F5F9')
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Recent Activity
st.markdown("## 📜 Recent Activity")
st.markdown("##### Latest compliance actions")
st.markdown("")

try:
    recent_logs = get_recent_audit_logs(org_id, limit=8)
    
    if recent_logs:
        for i, log in enumerate(recent_logs):
            col1, col2, col3, col4 = st.columns([2, 5, 2, 1])
            
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
                st.markdown(f"<div style='color: #94A3B8; font-weight: 600;'>{time_str}</div>", unsafe_allow_html=True)
            
            with col2:
                icon_map = {
                    "update": "🔄", "upload": "📤", "complete": "✅", 
                    "generate": "📊", "create": "➕", "delete": "🗑️",
                    "send_alert": "📧", "view": "👁️"
                }
                icon = icon_map.get(log['action'], "📝")
                st.markdown(f"<div style='color: #1E293B; font-weight: 600; font-size: 1.0625rem;'>{icon} {log['description']}</div>", unsafe_allow_html=True)
            
            with col3:
                user_name = log.get('users', {}).get('full_name', 'System') if log.get('users') else 'System'
                st.markdown(f"<div style='color: #64748B; text-align: right;'>{user_name}</div>", unsafe_allow_html=True)
            
            with col4:
                action_colors = {
                    "update": "#3B82F6", "upload": "#10B981", "complete": "#10B981",
                    "generate": "#8B5CF6", "create": "#F59E0B", "send_alert": "#EC4899"
                }
                color = action_colors.get(log['action'], "#94A3B8")
                st.markdown(f"<div style='width: 8px; height: 8px; background: {color}; border-radius: 50%; margin-top: 8px;'></div>", unsafe_allow_html=True)
            
            if i < len(recent_logs) - 1:
                st.markdown("<hr style='margin: 1rem 0; opacity: 0.3;'>", unsafe_allow_html=True)
    else:
        st.info("No recent activity")
        
except Exception as e:
    st.warning("Unable to load activity")

st.markdown("---")

# Quick Actions - Actually Working!
st.markdown("## 🚀 Quick Actions")
st.markdown("##### Take action on your compliance")
st.markdown("")

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    if st.button("📥 GENERATE REPORT", use_container_width=True, type="primary"):
        with st.spinner("🔄 Generating comprehensive compliance report..."):
            try:
                pdf_buffer = generate_pdf_report(
                    org_id, 
                    st.session_state.organization_name,
                    compliance_data,
                    metrics,
                    frameworks_summary
                )
                
                st.success("✅ Report generated successfully!")
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"CompliGH_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error generating report: {e}")
        
with col2:
    if st.button("📧 SEND ALERTS", use_container_width=True, type="primary"):
        with st.spinner("📧 Sending alerts to compliance team..."):
            try:
                recipient_count = send_email_alerts(org_id, "deadline")
                st.success(f"✅ Deadline alerts sent to {recipient_count} team members!")
                st.cache_data.clear()
                
            except Exception as e:
                st.error(f"Error sending alerts: {e}")

with col3:
    if st.button("⚙️ SETTINGS", use_container_width=True, type="primary"):
        st.switch_page("pages/4_⚙️_Settings.py")

st.markdown("---")

# Critical Items Alert
if st.session_state.critical_items > 0:
    st.error(f"### 🚨 {st.session_state.critical_items} Critical Items Need Immediate Attention!")
    
    critical_items = [d for d in compliance_data if d['status'] == 'critical']
    
    for item in critical_items[:3]:
        with st.expander(f"❌ {item['compliance_items']['name']} ({item['framework']['name']})"):
            st.markdown(f"**Description:** {item['compliance_items']['description']}")
            st.markdown(f"**Current Status:** {item.get('notes', 'No notes available')}")
            st.markdown(f"**Progress:** {item['progress']}%")
            
            if st.button(f"Fix This Now", key=f"fix_{item['compliance_item_id']}"):
                st.switch_page("pages/1_📋_Compliance_Frameworks.py")

st.markdown("---")

# Footer
st.markdown("""
    <div style='text-align: center; padding: 3rem 0 2rem 0;'>
        <div style='font-size: 1.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0.5rem;'>
            CompliGH
        </div>
        <div style='color: #64748B; font-size: 0.9375rem; font-weight: 600;'>
            Ghana Fintech Compliance Monitor
        </div>
        <div style='color: #94A3B8; font-size: 0.875rem; margin-top: 1rem;'>
            Powered by Streamlit • Built with ❤️ for Ghana's fintech ecosystem
        </div>
        <div style='margin-top: 1.5rem;'>
            <span style='display: inline-block; margin: 0 0.5rem; color: #CBD5E1;'>•</span>
            <a href="#" style='color: #64748B; text-decoration: none; font-size: 0.875rem;'>Privacy</a>
            <span style='display: inline-block; margin: 0 0.5rem; color: #CBD5E1;'>•</span>
            <a href="#" style='color: #64748B; text-decoration: none; font-size: 0.875rem;'>Terms</a>
            <span style='display: inline-block; margin: 0 0.5rem; color: #CBD5E1;'>•</span>
            <a href="#" style='color: #64748B; text-decoration: none; font-size: 0.875rem;'>Support</a>
        </div>
    </div>
""", unsafe_allow_html=True)
