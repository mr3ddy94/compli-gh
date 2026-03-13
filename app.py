"""
CompliGH Enterprise - Production SaaS Platform
Fixed Version with Proper Rendering
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.database import get_supabase_client
import io

# Page configuration
st.set_page_config(
    page_title="CompliGH Enterprise",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DATABASE ABSTRACTION LAYER
# =============================================================================

class ComplianceDataAdapter:
    def __init__(self, backend='supabase'):
        self.backend = backend
        if backend == 'supabase':
            self.client = get_supabase_client()
    
    def get_organization(self, org_id):
        if self.backend == 'supabase':
            response = self.client.table('organizations').select('*').eq('id', org_id).execute()
            return response.data[0] if response.data else None
    
    def get_frameworks(self, filters=None):
        if self.backend == 'supabase':
            query = self.client.table('frameworks').select('*')
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.order('priority_level').execute()
            return response.data
    
    def get_compliance_items(self, framework_id):
        if self.backend == 'supabase':
            response = self.client.table('compliance_items').select('*').eq(
                'framework_id', framework_id
            ).execute()
            return response.data
    
    def get_compliance_status(self, org_id, framework_id=None):
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
            
            response = query.execute()
            
            if framework_id:
                return [item for item in response.data 
                       if item['compliance_items']['framework_id'] == framework_id]
            
            return response.data
    
    def update_compliance_status(self, item_id, org_id, status, progress, notes, user_id):
        if self.backend == 'supabase':
            self.client.table('compliance_status').update({
                'status': status,
                'progress': progress,
                'notes': notes,
                'last_updated_by': user_id,
                'last_updated_at': datetime.now().isoformat()
            }).eq('compliance_item_id', item_id).eq('organization_id', org_id).execute()
            
            self.client.table('audit_logs').insert({
                'organization_id': org_id,
                'user_id': user_id,
                'action': 'update',
                'entity_type': 'compliance_status',
                'entity_id': item_id,
                'description': f'Updated compliance status to {status}'
            }).execute()
            
            return True

@st.cache_resource
def get_data_adapter():
    return ComplianceDataAdapter(backend='supabase')

# =============================================================================
# BUSINESS LOGIC
# =============================================================================

def calculate_framework_metrics(compliance_items):
    if not compliance_items:
        return {'total': 0, 'compliant': 0, 'warning': 0, 'critical': 0, 'not_started': 0, 'score': 0}
    
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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
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
# SILVER/BLACK THEME
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: #F8FAFC;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: 1px solid #475569;
    }
    
    [data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #0F172A;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
    }
    
    .stButton>button {
        background: #3B82F6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background: #1E40AF;
        transform: translateY(-1px);
    }
    
    h1 {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    
    h2 {
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #EF4444 0%, #F59E0B 50%, #10B981 100%);
    }
    
    .stProgress > div > div {
        background-color: #E5E7EB;
        height: 8px;
        border-radius: 4px;
    }
    
    hr {
        border: none;
        height: 1px;
        background: #E2E8F0;
        margin: 2rem 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

if 'organization_id' not in st.session_state:
    st.session_state.organization_id = '11111111-1111-1111-1111-111111111111'

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'

if 'selected_framework_id' not in st.session_state:
    st.session_state.selected_framework_id = None

if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Chief Compliance Officer'

if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

def navigate_to_framework(framework_id):
    st.session_state.current_view = 'framework_detail'
    st.session_state.selected_framework_id = framework_id
    st.rerun()

def navigate_to_dashboard():
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
    st.info("Please ensure database is properly configured.")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("# CompliGH")
    st.markdown("### Enterprise Compliance")
    st.markdown("---")
    
    st.markdown("**Organization**")
    st.markdown(f"{org_data['name']}")
    st.caption(f"License: {org_data['license_number']}")
    
    st.markdown("---")
    
    st.markdown("**User**")
    st.markdown(f"{st.session_state.user_role}")
    
    st.markdown("---")
    
    if st.button("Dashboard", use_container_width=True, 
                 type="primary" if st.session_state.current_view == 'dashboard' else "secondary"):
        navigate_to_dashboard()
    
    st.markdown("---")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Updated: {datetime.now().strftime('%d %b %H:%M')}")

# =============================================================================
# MAIN CONTENT
# =============================================================================

if st.session_state.current_view == 'dashboard':
    # DASHBOARD VIEW
    
    st.title("Compliance Dashboard")
    st.caption(f"{org_data['name']} | {org_data['license_type']}")
    
    st.markdown("---")
    
    # Calculate metrics
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
        st.metric("Risk Level", risk_level)
    
    with col4:
        st.metric("Critical Issues", overall_metrics['critical'])
    
    st.markdown("---")
    
    # Frameworks
    st.subheader("Regulatory Frameworks")
    st.caption("Click any framework to view detailed compliance status")
    
    st.markdown("")
    
    # Create framework cards in 2 columns
    col1, col2 = st.columns(2)
    
    for idx, framework in enumerate(frameworks_list):
        framework_compliance = adapter.get_compliance_status(org_id, framework['id'])
        metrics = calculate_framework_metrics(framework_compliance)
        
        with col1 if idx % 2 == 0 else col2:
            # Use container instead of HTML
            with st.container():
                st.markdown(f"### {framework['name']}")
                st.caption(framework['regulatory_body'])
                
                # Score and status
                score = metrics['score']
                
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.metric("Compliance Score", f"{score}%")
                with col_b:
                    if score >= 80:
                        st.success("COMPLIANT")
                    elif score >= 60:
                        st.warning("REVIEW")
                    else:
                        st.error("ACTION REQUIRED")
                
                # Stats
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("✓", metrics['compliant'], help="Compliant")
                with col_b:
                    st.metric("⚠", metrics['warning'], help="Warning")
                with col_c:
                    st.metric("✗", metrics['critical'], help="Critical")
                
                # Progress bar
                st.progress(score / 100)
                
                # Button
                if st.button(f"View Details →", key=f"fw_{framework['id']}", 
                            use_container_width=True, type="primary"):
                    navigate_to_framework(framework['id'])
                
                st.markdown("---")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Generate Report", use_container_width=True, type="primary"):
            with st.spinner("Generating..."):
                pdf = generate_pdf_report(org_data, all_compliance)
                st.download_button(
                    "Download PDF",
                    pdf,
                    file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with col2:
        if st.button("Export CSV", use_container_width=True):
            df = pd.DataFrame([{
                'Framework': item['compliance_items']['framework_id'],
                'Requirement': item['compliance_items']['title'],
                'Status': item['status'],
                'Progress': item['progress']
            } for item in all_compliance])
            
            csv = df.to_csv(index=False)
            st.download_button(
                "Download",
                csv,
                file_name=f"data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("Settings", use_container_width=True):
            st.info("Settings page - coming soon")

elif st.session_state.current_view == 'framework_detail':
    # FRAMEWORK DETAIL VIEW
    
    framework_id = st.session_state.selected_framework_id
    
    if not framework_id:
        st.error("No framework selected")
        if st.button("Return to Dashboard"):
            navigate_to_dashboard()
        st.stop()
    
    framework = next((f for f in frameworks_list if f['id'] == framework_id), None)
    
    if not framework:
        st.error("Framework not found")
        if st.button("Return to Dashboard"):
            navigate_to_dashboard()
        st.stop()
    
    # Header
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(framework['name'])
        st.caption(f"{framework['regulatory_body']} | {framework['description']}")
    
    with col2:
        if st.button("← Back", use_container_width=True):
            navigate_to_dashboard()
    
    st.markdown("---")
    
    # Get data
    framework_compliance = adapter.get_compliance_status(org_id, framework_id)
    metrics = calculate_framework_metrics(framework_compliance)
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Score", f"{metrics['score']}%")
    with col2:
        st.metric("Total", metrics['total'])
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
    
    # Display by category
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
                
                st.markdown(f"#### [{req_code}] {title}")
                
                if description:
                    st.caption(description)
                
                # Status and progress
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.progress(progress / 100)
                    st.caption(f"Progress: {progress}%")
                
                with col2:
                    if status == 'compliant':
                        st.success("Compliant")
                    elif status == 'warning':
                        st.warning("Warning")
                    elif status == 'critical':
                        st.error("Critical")
                    else:
                        st.info("Not Started")
                
                if notes:
                    st.info(f"Notes: {notes}")
                
                # Action buttons
                can_edit = st.session_state.user_role in ['Chief Compliance Officer', 'Senior Compliance Officer']
                
                if can_edit:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Update Status", key=f"update_{item['id']}", use_container_width=True):
                            st.session_state[f'editing_{item["id"]}'] = True
                            st.rerun()
                    
                    with col2:
                        if st.button("Upload Document", key=f"upload_{item['id']}", use_container_width=True):
                            st.info("Document upload - coming soon")
                    
                    with col3:
                        if st.button("View History", key=f"history_{item['id']}", use_container_width=True):
                            st.info("Audit history - coming soon")
                    
                    # Edit form
                    if st.session_state.get(f'editing_{item["id"]}', False):
                        with st.form(f"edit_form_{item['id']}"):
                            st.markdown("#### Update Status")
                            
                            new_status = st.selectbox(
                                "Status",
                                ["compliant", "warning", "critical", "not_started"],
                                index=["compliant", "warning", "critical", "not_started"].index(status)
                            )
                            
                            new_progress = st.slider("Progress (%)", 0, 100, progress)
                            new_notes = st.text_area("Notes", value=notes)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.form_submit_button("Save", use_container_width=True):
                                    adapter.update_compliance_status(
                                        item['compliance_item_id'],
                                        org_id,
                                        new_status,
                                        new_progress,
                                        new_notes,
                                        st.session_state.current_user_id
                                    )
                                    st.success("Updated!")
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
st.caption("CompliGH Enterprise | Confidential")
st.caption(f"© {datetime.now().year} CompliGH Ltd.")
