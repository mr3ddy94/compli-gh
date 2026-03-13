"""
CompliGH Enterprise - Multi-Tenant Compliance SaaS Platform
Production-Ready Architecture for Pan-African Deployment
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
    page_title="CompliGH Enterprise | Compliance Management",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DATABASE ABSTRACTION LAYER (For future cloud/on-prem support)
# =============================================================================

class ComplianceDataAdapter:
    """
    Abstraction layer for compliance data access
    Allows switching between SQL, NoSQL, Cloud APIs, On-Prem databases
    """
    
    def __init__(self, backend='supabase'):
        self.backend = backend
        if backend == 'supabase':
            self.client = get_supabase_client()
    
    def get_organization(self, org_id):
        """Fetch organization - adaptable to any backend"""
        if self.backend == 'supabase':
            response = self.client.table('organizations').select('*').eq('id', org_id).execute()
            return response.data[0] if response.data else None
        # Add other backends: MongoDB, MySQL, REST API, etc.
    
    def get_frameworks(self, filters=None):
        """Fetch frameworks - works with any database structure"""
        if self.backend == 'supabase':
            query = self.client.table('frameworks').select('*')
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.order('priority_level').execute()
            return response.data
    
    def get_compliance_items(self, framework_id):
        """Get all items for a framework"""
        if self.backend == 'supabase':
            response = self.client.table('compliance_items').select('*').eq(
                'framework_id', framework_id
            ).execute()
            return response.data
    
    def get_compliance_status(self, org_id, framework_id=None):
        """Get compliance status with framework filter"""
        if self.backend == 'supabase':
            query = self.client.table('compliance_status').select(
                '''
                *,
                compliance_items(
                    id, requirement_code, title, description, requirement_details,
                    criticality, frequency, category, framework_id
                ),
                assigned_to_user:assigned_to(full_name, email, role)
                '''
            ).eq('organization_id', org_id)
            
            if framework_id:
                # Filter by framework through join
                response = query.execute()
                return [item for item in response.data 
                       if item['compliance_items']['framework_id'] == framework_id]
            
            response = query.execute()
            return response.data
    
    def update_compliance_status(self, item_id, org_id, status, progress, notes, user_id):
        """Update compliance status with audit trail"""
        if self.backend == 'supabase':
            # Update status
            self.client.table('compliance_status').update({
                'status': status,
                'progress': progress,
                'notes': notes,
                'last_updated_by': user_id,
                'last_updated_at': datetime.now().isoformat()
            }).eq('compliance_item_id', item_id).eq('organization_id', org_id).execute()
            
            # Log action
            self.client.table('audit_logs').insert({
                'organization_id': org_id,
                'user_id': user_id,
                'action': 'update',
                'entity_type': 'compliance_status',
                'entity_id': item_id,
                'description': f'Updated compliance status to {status}'
            }).execute()
            
            return True

# Initialize data adapter
@st.cache_resource
def get_data_adapter():
    return ComplianceDataAdapter(backend='supabase')

# =============================================================================
# BUSINESS LOGIC LAYER
# =============================================================================

def calculate_framework_metrics(compliance_items):
    """Calculate metrics for a framework"""
    if not compliance_items:
        return {
            'total': 0, 'compliant': 0, 'warning': 0, 'critical': 0,
            'not_started': 0, 'score': 0
        }
    
    total = len(compliance_items)
    compliant = len([d for d in compliance_items if d['status'] == 'compliant'])
    warning = len([d for d in compliance_items if d['status'] == 'warning'])
    critical = len([d for d in compliance_items if d['status'] == 'critical'])
    not_started = len([d for d in compliance_items if d['status'] == 'not_started'])
    
    score = int((compliant / total) * 100) if total > 0 else 0
    
    return {
        'total': total,
        'compliant': compliant,
        'warning': warning,
        'critical': critical,
        'not_started': not_started,
        'score': score
    }

def generate_pdf_report(org_data, compliance_data):
    """Generate compliance report - placeholder for now"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph(f"Compliance Report - {org_data['name']}", styles['Title']))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# =============================================================================
# PROFESSIONAL SILVER/BLACK THEME WITH BRAND COLOR SUPPORT
# =============================================================================

def get_theme_colors():
    """Get theme colors - brand color can be customized per client"""
    return {
        'primary': st.session_state.get('brand_color', '#3B82F6'),  # Customizable brand color
        'black': '#0F172A',
        'dark_gray': '#1E293B',
        'medium_gray': '#475569',
        'light_gray': '#94A3B8',
        'silver': '#CBD5E1',
        'light_silver': '#E2E8F0',
        'white': '#FFFFFF',
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444'
    }

colors = get_theme_colors()

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{ 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* Main Layout */
    .main {{
        background: linear-gradient(135deg, {colors['white']} 0%, {colors['light_silver']} 100%);
    }}
    
    /* Sidebar - Silver/Black Theme */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {colors['black']} 0%, {colors['dark_gray']} 100%);
        border-right: 1px solid {colors['silver']};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {colors['silver']} !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: {colors['white']} !important;
        font-weight: 700;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        font-size: 2.25rem;
        font-weight: 700;
        color: {colors['black']};
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 0.875rem;
        font-weight: 600;
        color: {colors['medium_gray']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Buttons */
    .stButton>button {{
        background: {colors['primary']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.2s;
        cursor: pointer;
    }}
    
    .stButton>button:hover {{
        background: {colors['black']};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
    }}
    
    /* Secondary Button */
    .stButton>button[kind="secondary"] {{
        background: {colors['silver']};
        color: {colors['black']};
    }}
    
    .stButton>button[kind="secondary"]:hover {{
        background: {colors['light_gray']};
    }}
    
    /* Typography */
    h1 {{
        color: {colors['black']} !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        letter-spacing: -0.02em !important;
    }}
    
    h2 {{
        color: {colors['dark_gray']} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid {colors['light_silver']};
    }}
    
    h3 {{
        color: {colors['medium_gray']} !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
    }}
    
    /* Framework Cards - Clickable */
    .framework-card {{
        background: {colors['white']};
        border: 2px solid {colors['light_silver']};
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
    }}
    
    .framework-card:hover {{
        border-color: {colors['primary']};
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
        transform: translateY(-4px);
    }}
    
    .framework-card:active {{
        transform: translateY(-2px);
    }}
    
    .framework-title {{
        font-size: 1.125rem;
        font-weight: 700;
        color: {colors['black']};
        margin-bottom: 0.5rem;
    }}
    
    .framework-subtitle {{
        font-size: 0.875rem;
        color: {colors['medium_gray']};
        margin-bottom: 1rem;
    }}
    
    .framework-score {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {colors['black']};
        line-height: 1;
    }}
    
    /* Status Badges */
    .status-badge {{
        display: inline-block;
        padding: 0.375rem 0.875rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .status-compliant {{
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }}
    
    .status-warning {{
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }}
    
    .status-critical {{
        background: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }}
    
    .status-not-started {{
        background: {colors['light_silver']};
        color: {colors['medium_gray']};
        border: 1px solid {colors['silver']};
    }}
    
    /* Stats Grid */
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid {colors['light_silver']};
    }}
    
    .stat-item {{
        text-align: center;
    }}
    
    .stat-value {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {colors['black']};
    }}
    
    .stat-label {{
        font-size: 0.75rem;
        color: {colors['medium_gray']};
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }}
    
    /* Progress Bars */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {colors['error']} 0%, {colors['warning']} 50%, {colors['success']} 100%);
    }}
    
    .stProgress > div > div {{
        background-color: {colors['light_silver']};
        height: 8px;
        border-radius: 4px;
    }}
    
    /* Alerts */
    .stSuccess {{
        background: #F0FDF4;
        border-left: 4px solid {colors['success']};
        color: #166534;
        padding: 1rem;
        border-radius: 6px;
    }}
    
    .stWarning {{
        background: #FFFBEB;
        border-left: 4px solid {colors['warning']};
        color: #92400E;
        padding: 1rem;
        border-radius: 6px;
    }}
    
    .stError {{
        background: #FEF2F2;
        border-left: 4px solid {colors['error']};
        color: #991B1B;
        padding: 1rem;
        border-radius: 6px;
    }}
    
    /* Tables */
    .dataframe {{
        border: 1px solid {colors['light_silver']} !important;
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .dataframe thead tr {{
        background: {colors['black']} !important;
        color: white !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background: {colors['light_silver']};
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: {colors['white']};
        border-bottom: 2px solid {colors['light_silver']};
        padding: 0 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 1rem 2rem;
        font-weight: 600;
        color: {colors['medium_gray']};
        border-radius: 0;
        background: transparent;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {colors['primary']};
        border-bottom: 3px solid {colors['primary']};
        background: transparent;
    }}
    
    /* Dividers */
    hr {{
        border: none;
        height: 1px;
        background: {colors['light_silver']};
        margin: 2rem 0;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .stats-grid {{
            grid-template-columns: 1fr;
        }}
        
        .framework-score {{
            font-size: 2rem;
        }}
    }}
    
    /* Loading States */
    .stSpinner > div {{
        border-top-color: {colors['primary']} !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background: {colors['white']};
        border: 1px solid {colors['light_silver']};
        border-radius: 6px;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: {colors['black']};
    }}
    
    .streamlit-expanderHeader:hover {{
        border-color: {colors['primary']};
        background: {colors['light_silver']};
    }}
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE & ROUTING
# =============================================================================

# Initialize session state
if 'organization_id' not in st.session_state:
    st.session_state.organization_id = '11111111-1111-1111-1111-111111111111'

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'

if 'selected_framework_id' not in st.session_state:
    st.session_state.selected_framework_id = None

if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Chief Compliance Officer'  # Admin, Officer, Viewer

if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

# Navigation functions
def navigate_to_framework(framework_id):
    """Navigate to framework detail view"""
    st.session_state.current_view = 'framework_detail'
    st.session_state.selected_framework_id = framework_id
    st.rerun()

def navigate_to_dashboard():
    """Navigate back to dashboard"""
    st.session_state.current_view = 'dashboard'
    st.session_state.selected_framework_id = None
    st.rerun()

# =============================================================================
# DATA LOADING
# =============================================================================

adapter = get_data_adapter()
org_id = st.session_state.organization_id

try:
    org_data = adapter.get_organization(org_id)
    frameworks_list = adapter.get_frameworks({'is_active': True})
    
    if not org_data:
        st.error("Organization not found. Please check configuration.")
        st.stop()
    
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("# CompliGH")
    st.markdown("### Enterprise Compliance SaaS")
    st.markdown("---")
    
    st.markdown("**Organization**")
    st.markdown(f"{org_data['name']}")
    st.caption(f"License: {org_data['license_number']}")
    
    st.markdown("---")
    
    st.markdown("**User**")
    st.markdown(f"{st.session_state.user_role}")
    st.caption("Access Level: Full")
    
    st.markdown("---")
    
    st.markdown("**Navigation**")
    
    if st.button("Dashboard", use_container_width=True, 
                 type="primary" if st.session_state.current_view == 'dashboard' else "secondary"):
        navigate_to_dashboard()
    
    if st.button("Frameworks", use_container_width=True,
                 type="primary" if st.session_state.current_view == 'framework_detail' else "secondary"):
        st.info("Select a framework from the dashboard")
    
    st.markdown("---")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Last Updated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
    st.caption("CompliGH Enterprise v2.5")

# =============================================================================
# MAIN CONTENT - ROUTING
# =============================================================================

if st.session_state.current_view == 'dashboard':
    # =========================================================================
    # DASHBOARD VIEW
    # =========================================================================
    
    st.title("Compliance Dashboard")
    st.caption(f"{org_data['name']} | {org_data['license_type']}")
    
    st.markdown("---")
    
    # Calculate overall metrics
    all_compliance = adapter.get_compliance_status(org_id)
    overall_metrics = calculate_framework_metrics(all_compliance)
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Compliance", f"{overall_metrics['score']}%")
    
    with col2:
        st.metric("Total Requirements", overall_metrics['total'])
    
    with col3:
        risk = min(overall_metrics['critical'] * 15 + overall_metrics['warning'] * 5, 100)
        risk_level = "Low" if risk < 25 else "Moderate" if risk < 50 else "High"
        st.metric("Risk Level", risk_level, f"{risk}/100")
    
    with col4:
        st.metric("Critical Issues", overall_metrics['critical'])
    
    st.markdown("---")
    
    # Frameworks Grid
    st.subheader("Regulatory Frameworks")
    st.caption("Click any framework to view detailed compliance status and manage requirements")
    
    st.markdown("")
    
    # Create 2-column layout
    col1, col2 = st.columns(2)
    
    for idx, framework in enumerate(frameworks_list):
        # Get compliance data for this framework
        framework_compliance = adapter.get_compliance_status(org_id, framework['id'])
        metrics = calculate_framework_metrics(framework_compliance)
        
        with col1 if idx % 2 == 0 else col2:
            score = metrics['score']
            
            status_class = "compliant" if score >= 80 else "warning" if score >= 60 else "critical"
            status_text = "COMPLIANT" if score >= 80 else "REVIEW NEEDED" if score >= 60 else "ACTION REQUIRED"
            
            # Render clickable framework card
            st.markdown(f"""
                <div class="framework-card" onclick="document.getElementById('fw_{framework['id']}').click()">
                    <div class="framework-title">{framework['name']}</div>
                    <div class="framework-subtitle">{framework['regulatory_body']}</div>
                    
                    <div style="margin: 1.5rem 0;">
                        <span class="framework-score">{score}%</span>
                    </div>
                    
                    <div style="margin: 1rem 0;">
                        <span class="status-badge status-{status_class}">{status_text}</span>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value">{metrics['compliant']}</div>
                            <div class="stat-label">Compliant</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{metrics['warning']}</div>
                            <div class="stat-label">Warning</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{metrics['critical']}</div>
                            <div class="stat-label">Critical</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Hidden button for navigation
            if st.button("View Framework", key=f"fw_{framework['id']}", 
                        use_container_width=True, type="primary"):
                navigate_to_framework(framework['id'])
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Generate Compliance Report", use_container_width=True, type="primary"):
            with st.spinner("Generating report..."):
                pdf = generate_pdf_report(org_data, all_compliance)
                st.download_button(
                    "Download PDF Report",
                    pdf,
                    file_name=f"Compliance_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with col2:
        if st.button("Export Data (CSV)", use_container_width=True):
            df = pd.DataFrame([{
                'Framework': item['compliance_items']['framework_id'],
                'Requirement': item['compliance_items']['title'],
                'Status': item['status'],
                'Progress': item['progress']
            } for item in all_compliance])
            
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
            st.info("Audit trail functionality - navigate to Audit page")

elif st.session_state.current_view == 'framework_detail':
    # =========================================================================
    # FRAMEWORK DETAIL VIEW
    # =========================================================================
    
    framework_id = st.session_state.selected_framework_id
    
    if not framework_id:
        st.error("No framework selected")
        if st.button("Return to Dashboard"):
            navigate_to_dashboard()
        st.stop()
    
    # Get framework data
    framework = next((f for f in frameworks_list if f['id'] == framework_id), None)
    
    if not framework:
        st.error("Framework not found")
        if st.button("Return to Dashboard"):
            navigate_to_dashboard()
        st.stop()
    
    # Header with back button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(framework['name'])
        st.caption(f"{framework['regulatory_body']} | {framework['description']}")
    
    with col2:
        if st.button("← Back to Dashboard", use_container_width=True, type="secondary"):
            navigate_to_dashboard()
    
    st.markdown("---")
    
    # Get compliance data
    framework_compliance = adapter.get_compliance_status(org_id, framework_id)
    compliance_items_data = adapter.get_compliance_items(framework_id)
    metrics = calculate_framework_metrics(framework_compliance)
    
    # Framework Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Compliance Score", f"{metrics['score']}%")
    with col2:
        st.metric("Total Items", metrics['total'])
    with col3:
        st.metric("Compliant", metrics['compliant'])
    with col4:
        st.metric("Warning", metrics['warning'])
    with col5:
        st.metric("Critical", metrics['critical'])
    
    st.markdown("---")
    
    # Group by category
    categories = {}
    for item in framework_compliance:
        cat = item['compliance_items'].get('category', 'Uncategorized')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # Display requirements by category
    st.subheader("Requirements by Category")
    
    for category, items in categories.items():
        cat_compliant = len([i for i in items if i['status'] == 'compliant'])
        cat_score = int((cat_compliant / len(items)) * 100) if items else 0
        
        with st.expander(f"{category} ({len(items)} items | {cat_score}% compliant)", expanded=True):
            
            for item in items:
                req_code = item['compliance_items'].get('requirement_code', 'N/A')
                title = item['compliance_items']['title']
                description = item['compliance_items'].get('description', '')
                status = item['status']
                progress = item['progress']
                notes = item.get('notes', '')
                assigned = item.get('assigned_to_user')
                
                # Create columns for layout
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### [{req_code}] {title}")
                    if description:
                        st.caption(description)
                    
                    # Show assignment
                    if assigned:
                        st.caption(f"Assigned to: {assigned.get('full_name', 'Unassigned')}")
                
                with col2:
                    # Status badge
                    status_class = {
                        'compliant': 'status-compliant',
                        'warning': 'status-warning',
                        'critical': 'status-critical',
                        'not_started': 'status-not-started'
                    }.get(status, 'status-not-started')
                    
                    status_text = status.replace('_', ' ').upper()
                    
                    st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', 
                               unsafe_allow_html=True)
                    
                    st.markdown("")
                    st.metric("Progress", f"{progress}%")
                
                # Progress bar
                st.progress(progress / 100)
                
                # Notes
                if notes:
                    st.info(f"**Notes:** {notes}")
                
                # Action buttons (role-based)
                can_edit = st.session_state.user_role in ['Chief Compliance Officer', 'Senior Compliance Officer']
                
                if can_edit:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Update Status", key=f"update_{item['id']}", use_container_width=True):
                            st.session_state[f'editing_{item["id"]}'] = True
                            st.rerun()
                    
                    with col2:
                        if st.button("Upload Document", key=f"upload_{item['id']}", use_container_width=True):
                            st.info("Document upload functionality coming soon")
                    
                    with col3:
                        if st.button("View History", key=f"history_{item['id']}", use_container_width=True):
                            st.info("Audit history functionality coming soon")
                    
                    # Edit form
                    if st.session_state.get(f'editing_{item["id"]}', False):
                        with st.form(f"edit_form_{item['id']}"):
                            st.markdown("#### Update Compliance Status")
                            
                            new_status = st.selectbox(
                                "Status",
                                ["compliant", "warning", "critical", "not_started"],
                                index=["compliant", "warning", "critical", "not_started"].index(status)
                            )
                            
                            new_progress = st.slider("Progress (%)", 0, 100, progress)
                            
                            new_notes = st.text_area("Notes", value=notes)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Save Changes", use_container_width=True):
                                    adapter.update_compliance_status(
                                        item['compliance_item_id'],
                                        org_id,
                                        new_status,
                                        new_progress,
                                        new_notes,
                                        st.session_state.current_user_id
                                    )
                                    st.success("Status updated successfully!")
                                    st.session_state[f'editing_{item["id"]}'] = False
                                    st.cache_data.clear()
                                    st.rerun()
                            
                            with col2:
                                if st.form_submit_button("Cancel", use_container_width=True):
                                    st.session_state[f'editing_{item["id"]}'] = False
                                    st.rerun()
                
                st.markdown("---")

# Footer
st.markdown("---")
st.caption("CompliGH Enterprise | Confidential & Proprietary")
st.caption(f"© {datetime.now().year} CompliGH Ltd. All rights reserved.")
