"""
CompliGH - Enterprise Compliance Monitoring Platform
Production-Ready Version for Ghana Fintech
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.database import get_supabase_client
import io

# Page configuration
st.set_page_config(
    page_title="CompliGH Enterprise | Compliance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

@st.cache_data(ttl=30)
def get_compliance_summary(org_id):
    """Fetch comprehensive compliance data"""
    supabase = get_supabase_client()
    
    response = supabase.table('compliance_status').select(
        '''
        *,
        compliance_items(
            id, requirement_code, title, description, requirement_details,
            criticality, frequency, category, penalty_description,
            framework_id
        ),
        assigned_to_user:assigned_to(full_name, email)
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


@st.cache_data(ttl=300)
def get_frameworks():
    """Fetch all active frameworks"""
    supabase = get_supabase_client()
    response = supabase.table('frameworks').select('*').eq('is_active', True).order('priority_level').execute()
    return response.data


def calculate_metrics(compliance_data):
    """Calculate comprehensive compliance metrics"""
    if not compliance_data:
        return {
            'total_items': 0, 'compliant': 0, 'warning': 0, 'critical': 0,
            'not_started': 0, 'compliance_score': 0, 'risk_score': 100,
            'critical_items_count': 0, 'high_items_count': 0
        }
    
    total = len(compliance_data)
    compliant = len([d for d in compliance_data if d['status'] == 'compliant'])
    warning = len([d for d in compliance_data if d['status'] == 'warning'])
    critical = len([d for d in compliance_data if d['status'] == 'critical'])
    not_started = len([d for d in compliance_data if d['status'] == 'not_started'])
    
    # Count by criticality
    critical_items = len([d for d in compliance_data if d['compliance_items']['criticality'] == 'critical'])
    high_items = len([d for d in compliance_data if d['compliance_items']['criticality'] == 'high'])
    
    compliance_score = int((compliant / total) * 100) if total > 0 else 0
    
    # Weighted risk score
    risk_score = 0
    if total > 0:
        critical_risk = (critical / total) * 40
        warning_risk = (warning / total) * 25
        not_started_risk = (not_started / total) * 35
        risk_score = min(critical_risk + warning_risk + not_started_risk, 100)
    
    return {
        'total_items': total,
        'compliant': compliant,
        'warning': warning,
        'critical': critical,
        'not_started': not_started,
        'compliance_score': compliance_score,
        'risk_score': int(risk_score),
        'critical_items_count': critical_items,
        'high_items_count': high_items
    }


def get_framework_compliance(compliance_data, framework_id):
    """Get detailed compliance for specific framework"""
    framework_items = [d for d in compliance_data if d.get('framework') and d['framework']['id'] == framework_id]
    
    if not framework_items:
        return None
    
    total = len(framework_items)
    compliant = len([d for d in framework_items if d['status'] == 'compliant'])
    warning = len([d for d in framework_items if d['status'] == 'warning'])
    critical = len([d for d in framework_items if d['status'] == 'critical'])
    not_started = len([d for d in framework_items if d['status'] == 'not_started'])
    
    score = int((compliant / total) * 100) if total > 0 else 0
    
    # Group by category
    categories = {}
    for item in framework_items:
        cat = item['compliance_items'].get('category', 'Uncategorized')
        if cat not in categories:
            categories[cat] = {'total': 0, 'compliant': 0, 'warning': 0, 'critical': 0}
        categories[cat]['total'] += 1
        categories[cat][item['status']] = categories[cat].get(item['status'], 0) + 1
    
    return {
        'framework': framework_items[0]['framework'],
        'total': total,
        'compliant': compliant,
        'warning': warning,
        'critical': critical,
        'not_started': not_started,
        'score': score,
        'items': framework_items,
        'categories': categories
    }


def generate_pdf_report(org_data, compliance_data, metrics):
    """Generate professional PDF compliance report"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=0.3*cm,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=1*cm,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        fontSize=14,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=0.5*cm,
        spaceBefore=0.8*cm,
        fontName='Helvetica-Bold'
    )
    
    # Header
    story.append(Paragraph("COMPLIANCE STATUS REPORT", title_style))
    story.append(Paragraph(f"{org_data['name']}", subtitle_style))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    story.append(Paragraph(f"License: {org_data['license_number']}", styles['Normal']))
    story.append(Spacer(1, 0.8*cm))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    
    summary_data = [
        ['Metric', 'Value', 'Assessment'],
        ['Overall Compliance Score', f"{metrics['compliance_score']}%", 
         'EXCELLENT' if metrics['compliance_score'] >= 90 else 'GOOD' if metrics['compliance_score'] >= 75 else 'REQUIRES ATTENTION'],
        ['Total Requirements', str(metrics['total_items']), '-'],
        ['Fully Compliant', str(metrics['compliant']), 'GREEN'],
        ['Partial Compliance', str(metrics['warning']), 'AMBER'],
        ['Non-Compliant', str(metrics['critical']), 'RED' if metrics['critical'] > 0 else 'NONE'],
        ['Risk Score', f"{metrics['risk_score']}/100", 
         'LOW' if metrics['risk_score'] < 25 else 'MODERATE' if metrics['risk_score'] < 50 else 'HIGH'],
        ['Critical Requirements', str(metrics['critical_items_count']), '-'],
        ['High Priority Requirements', str(metrics['high_items_count']), '-']
    ]
    
    summary_table = Table(summary_data, colWidths=[6*cm, 4*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 1*cm))
    
    # Critical Non-Compliance
    critical_items = [d for d in compliance_data if d['status'] == 'critical']
    if critical_items:
        story.append(Paragraph("CRITICAL NON-COMPLIANCE ITEMS", heading_style))
        story.append(Paragraph(
            "The following items require immediate remediation:",
            ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#DC2626'))
        ))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, item in enumerate(critical_items[:10], 1):
            story.append(Paragraph(
                f"{idx}. <b>{item['compliance_items']['title']}</b> ({item['framework']['name']})",
                styles['Normal']
            ))
            story.append(Paragraph(
                f"   Status: {item['status'].upper()} | Progress: {item['progress']}%",
                ParagraphStyle('Detail', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748B'))
            ))
            story.append(Spacer(1, 0.2*cm))
    
    # Recommendations
    story.append(PageBreak())
    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    
    recommendations = []
    if metrics['critical'] > 0:
        recommendations.append(f"IMMEDIATE: Address {metrics['critical']} non-compliant requirements within 30 days")
    if metrics['warning'] > 5:
        recommendations.append(f"HIGH PRIORITY: Complete {metrics['warning']} partially compliant items within 60 days")
    if metrics['compliance_score'] < 85:
        recommendations.append("STRATEGIC: Implement quarterly compliance review cycles")
    recommendations.append("ONGOING: Maintain real-time compliance monitoring")
    recommendations.append("GOVERNANCE: Quarterly board reporting on compliance status")
    
    for idx, rec in enumerate(recommendations, 1):
        story.append(Paragraph(f"{idx}. {rec}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"This report is confidential and intended solely for {org_data['name']}",
        ParagraphStyle('Footer', fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        "CompliGH Enterprise Compliance Platform | www.compligh.com",
        ParagraphStyle('Footer2', fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =============================================================================
# PROFESSIONAL UI - NO EMOJIS, CLEAN DESIGN
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    
    /* Main background */
    .main {
        background: #F8FAFC;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.25rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.8125rem;
        font-weight: 500;
    }
    
    /* Buttons */
    .stButton>button {
        background: #1E3A8A;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
        letter-spacing: 0.01em;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .stButton>button:hover {
        background: #1E40AF;
        box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2);
        transform: translateY(-1px);
    }
    
    /* Typography */
    h1 {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        letter-spacing: -0.01em !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #E2E8F0;
    }
    
    h3 {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    p, .stMarkdown {
        color: #475569;
        font-size: 0.9375rem;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Framework Cards */
    .framework-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .framework-card:hover {
        border-color: #1E3A8A;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.08);
        transform: translateY(-2px);
    }
    
    .framework-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #F1F5F9;
    }
    
    .framework-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1E293B;
        margin: 0;
    }
    
    .framework-score {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-compliant {
        background: #DCFCE7;
        color: #166534;
    }
    
    .status-warning {
        background: #FEF3C7;
        color: #92400E;
    }
    
    .status-critical {
        background: #FEE2E2;
        color: #991B1B;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #F1F5F9;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        display: block;
    }
    
    .stat-label {
        font-size: 0.6875rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #DC2626 0%, #F59E0B 50%, #10B981 100%);
    }
    
    .stProgress > div > div {
        background-color: #E5E7EB;
        height: 6px;
    }
    
    /* Alerts */
    .stSuccess {
        background: #F0FDF4;
        border-left: 4px solid #10B981;
        color: #065F46;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .stWarning {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        color: #92400E;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .stError {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        color: #991B1B;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .stInfo {
        background: #EFF6FF;
        border-left: 4px solid #2563EB;
        color: #1E40AF;
        padding: 1rem;
        border-radius: 4px;
    }
    
    /* Remove default padding */
    .block-container {
        padding: 2rem 2rem;
        max-width: 1400px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: #E2E8F0;
        margin: 2rem 0;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.875rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: white;
        border-bottom: 2px solid #E2E8F0;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #64748B;
        border-radius: 0;
    }
    
    .stTabs [aria-selected="true"] {
        color: #1E3A8A;
        border-bottom: 2px solid #1E3A8A;
        background: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE & DATA LOADING
# =============================================================================

if 'organization_id' not in st.session_state:
    st.session_state.organization_id = '11111111-1111-1111-1111-111111111111'

if 'selected_framework' not in st.session_state:
    st.session_state.selected_framework = None

org_id = st.session_state.organization_id

try:
    org_data = get_organization(org_id)
    compliance_data = get_compliance_summary(org_id)
    frameworks_list = get_frameworks()
    metrics = calculate_metrics(compliance_data)
    
    if not org_data:
        st.error("Organization not found. Please check database configuration.")
        st.stop()
    
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Please ensure database schema is properly configured.")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("# CompliGH")
    st.markdown("#### Enterprise Compliance Platform")
    st.markdown("---")
    
    st.markdown("### Organization")
    st.markdown(f"**{org_data['name']}**")
    st.caption(f"License: {org_data['license_number']}")
    
    st.markdown("---")
    
    st.markdown("### Compliance Overview")
    
    score = metrics['compliance_score']
    if score >= 90:
        st.success(f"**{score}%** - Excellent")
    elif score >= 75:
        st.info(f"**{score}%** - Good")
    elif score >= 60:
        st.warning(f"**{score}%** - Fair")
    else:
        st.error(f"**{score}%** - Critical")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", metrics['total_items'])
        st.metric("Compliant", metrics['compliant'])
    with col2:
        st.metric("Warning", metrics['warning'])
        st.metric("Critical", metrics['critical'])
    
    st.markdown("---")
    
    st.markdown("### Last Updated")
    st.caption(datetime.now().strftime("%d %b %Y, %H:%M"))
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("CompliGH Enterprise v2.0")

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

# Check if viewing specific framework
if st.session_state.selected_framework:
    framework_detail = get_framework_compliance(compliance_data, st.session_state.selected_framework)
    
    if framework_detail:
        # Framework Detail View
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(framework_detail['framework']['name'])
            st.caption(f"{framework_detail['framework']['description']}")
        
        with col2:
            if st.button("← Back to Dashboard", use_container_width=True):
                st.session_state.selected_framework = None
                st.rerun()
        
        st.markdown("---")
        
        # Framework Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Compliance Score", f"{framework_detail['score']}%")
        with col2:
            st.metric("Total Items", framework_detail['total'])
        with col3:
            st.metric("Compliant", framework_detail['compliant'])
        with col4:
            st.metric("Warning", framework_detail['warning'])
        with col5:
            st.metric("Critical", framework_detail['critical'])
        
        st.markdown("---")
        
        # Categories Breakdown
        st.subheader("Requirements by Category")
        
        for category, cat_stats in framework_detail['categories'].items():
            with st.expander(f"{category} ({cat_stats['total']} items)", expanded=True):
                
                cat_compliant = cat_stats.get('compliant', 0)
                cat_score = int((cat_compliant / cat_stats['total']) * 100) if cat_stats['total'] > 0 else 0
                
                st.progress(cat_score / 100)
                st.caption(f"{cat_score}% compliant")
                
                # Show items in this category
                category_items = [item for item in framework_detail['items'] 
                                if item['compliance_items'].get('category') == category]
                
                for item in category_items:
                    req_code = item['compliance_items'].get('requirement_code', 'N/A')
                    title = item['compliance_items']['title']
                    status = item['status']
                    progress = item['progress']
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**[{req_code}]** {title}")
                        if item['compliance_items'].get('requirement_details'):
                            st.caption(item['compliance_items']['requirement_details'][:150] + "...")
                    
                    with col2:
                        if status == 'compliant':
                            st.success("Compliant")
                        elif status == 'warning':
                            st.warning("Warning")
                        elif status == 'critical':
                            st.error("Critical")
                        else:
                            st.info("Not Started")
                    
                    with col3:
                        st.metric("Progress", f"{progress}%")
                    
                    if item.get('notes'):
                        st.caption(f"Notes: {item['notes']}")
                    
                    st.markdown("---")
        
        # Export button
        if st.button("Export Framework Report", use_container_width=True, type="primary"):
            st.info("Framework-specific export functionality coming soon")
    
    else:
        st.error("Framework data not found")
        if st.button("← Back to Dashboard"):
            st.session_state.selected_framework = None
            st.rerun()

else:
    # Main Dashboard View
    st.title("Compliance Dashboard")
    st.caption(f"{org_data['name']} | {org_data['license_type']}")
    
    st.markdown("---")
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall Compliance",
            f"{metrics['compliance_score']}%",
            "+3%" if metrics['compliance_score'] >= 75 else "-5%"
        )
    
    with col2:
        st.metric(
            "Total Requirements",
            metrics['total_items'],
            f"{metrics['compliant']} compliant"
        )
    
    with col3:
        risk_level = "Low" if metrics['risk_score'] < 25 else "Moderate" if metrics['risk_score'] < 50 else "High"
        st.metric(
            "Risk Level",
            risk_level,
            f"{metrics['risk_score']}/100"
        )
    
    with col4:
        st.metric(
            "Critical Issues",
            metrics['critical'],
            "Immediate action required" if metrics['critical'] > 0 else "None"
        )
    
    st.markdown("---")
    
    # Frameworks Grid
    st.subheader("Regulatory Frameworks")
    st.caption("Click any framework to view detailed compliance status")
    
    # Create 2 columns for frameworks
    col1, col2 = st.columns(2)
    
    for idx, framework in enumerate(frameworks_list):
        framework_comp = get_framework_compliance(compliance_data, framework['id'])
        
        if not framework_comp:
            continue
        
        with col1 if idx % 2 == 0 else col2:
            score = framework_comp['score']
            
            status_class = "compliant" if score >= 80 else "warning" if score >= 60 else "critical"
            status_text = "COMPLIANT" if score >= 80 else "REVIEW NEEDED" if score >= 60 else "ACTION REQUIRED"
            
            st.markdown(f"""
                <div class="framework-card">
                    <div class="framework-header">
                        <div>
                            <div class="framework-title">{framework['name']}</div>
                            <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.25rem;">
                                {framework['regulatory_body']}
                            </div>
                        </div>
                        <div class="framework-score">{score}%</div>
                    </div>
                    <div style="margin-bottom: 0.75rem;">
                        <span class="status-badge status-{status_class}">{status_text}</span>
                    </div>
                    <div class="stat-row">
                        <div class="stat-item">
                            <span class="stat-value">{framework_comp['compliant']}</span>
                            <span class="stat-label">Compliant</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">{framework_comp['warning']}</span>
                            <span class="stat-label">Warning</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">{framework_comp['critical']}</span>
                            <span class="stat-label">Critical</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.progress(score / 100)
            
            if st.button(f"View Details →", key=f"fw_{framework['id']}", use_container_width=True):
                st.session_state.selected_framework = framework['id']
                st.rerun()
    
    st.markdown("---")
    
    # Critical Items Alert
    if metrics['critical'] > 0:
        st.error(f"**{metrics['critical']} Critical Items Require Immediate Attention**")
        
        critical_items = [d for d in compliance_data if d['status'] == 'critical'][:5]
        
        for item in critical_items:
            with st.expander(f"[{item['compliance_items'].get('requirement_code', 'N/A')}] {item['compliance_items']['title']}"):
                st.markdown(f"**Framework:** {item['framework']['name']}")
                st.markdown(f"**Description:** {item['compliance_items']['description']}")
                st.markdown(f"**Progress:** {item['progress']}%")
                if item.get('notes'):
                    st.markdown(f"**Notes:** {item['notes']}")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Generate Compliance Report", use_container_width=True, type="primary"):
            with st.spinner("Generating comprehensive report..."):
                try:
                    pdf = generate_pdf_report(org_data, compliance_data, metrics)
                    st.success("Report generated successfully")
                    st.download_button(
                        "Download PDF Report",
                        pdf,
                        file_name=f"Compliance_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    with col2:
        if st.button("Export Data (CSV)", use_container_width=True):
            df = pd.DataFrame([{
                'Framework': d['framework']['name'],
                'Requirement': d['compliance_items']['title'],
                'Status': d['status'],
                'Progress': d['progress'],
                'Criticality': d['compliance_items']['criticality']
            } for d in compliance_data])
            
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                file_name=f"compliance_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("View Audit Trail", use_container_width=True):
            st.switch_page("pages/3_📜_Audit_Trail.py")

# Footer
st.markdown("---")
st.caption("CompliGH Enterprise Compliance Platform | Confidential")
