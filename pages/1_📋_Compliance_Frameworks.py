import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_supabase_client

st.set_page_config(page_title="Compliance Frameworks", page_icon="📋", layout="wide")

# Apply same improved CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #FFFFFF; }
    
    h1 { color: #0F172A !important; font-weight: 900 !important; font-size: 3rem !important; }
    h2 { color: #1E293B !important; font-weight: 800 !important; border-bottom: 3px solid #D97706; padding-bottom: 0.5rem; }
    h3 { color: #334155 !important; font-weight: 700 !important; }
    
    .stButton>button {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: #FFFFFF;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #B45309 0%, #92400E 100%);
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.5);
        transform: translateY(-3px);
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #D97706 0%, #FBBF24 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background-color: #E2E8F0;
        border-radius: 10px;
        height: 12px;
    }
    
    .stSuccess {
        background-color: #D1FAE5;
        border-left: 6px solid #059669;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #064E3B;
        font-weight: 700;
        font-size: 1.0625rem;
    }
    
    .stWarning {
        background-color: #FEF3C7;
        border-left: 6px solid #D97706;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #78350F;
        font-weight: 700;
        font-size: 1.0625rem;
    }
    
    .stError {
        background-color: #FEE2E2;
        border-left: 6px solid #DC2626;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #7F1D1D;
        font-weight: 700;
        font-size: 1.0625rem;
    }
    
    .stInfo {
        background-color: #DBEAFE;
        border-left: 6px solid #2563EB;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        color: #1E3A8A;
        font-weight: 700;
        font-size: 1.0625rem;
    }
    
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
        font-size: 1rem;
        border: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: white;
        border-color: #92400E;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
    }
    
    p, .stMarkdown {
        color: #334155;
        font-size: 1.0625rem;
        font-weight: 500;
        line-height: 1.8;
    }
    
    .stCaption {
        color: #64748B;
        font-size: 0.9375rem;
        font-weight: 600;
    }
    
    hr {
        margin: 3rem 0;
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent, #D97706, transparent);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0F172A;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

@st.cache_data(ttl=30)
def get_compliance_data(org_id):
    """Fetch all compliance data for organization"""
    supabase = get_supabase_client()
    
    response = supabase.table('compliance_status').select(
        '''
        *,
        compliance_items(
            id,
            name,
            description,
            criticality,
            framework_id,
            requirement_code
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


def update_compliance_status(item_id, org_id, new_status, progress, notes):
    """Update compliance status in database"""
    supabase = get_supabase_client()
    
    try:
        update_data = {
            'status': new_status,
            'progress': progress,
            'notes': notes,
            'last_updated_at': datetime.now().isoformat()
        }
        
        supabase.table('compliance_status').update(update_data).eq(
            'compliance_item_id', item_id
        ).eq('organization_id', org_id).execute()
        
        supabase.table('audit_logs').insert({
            'organization_id': org_id,
            'action': 'update',
            'entity_type': 'compliance_item',
            'entity_id': item_id,
            'description': f'Updated status to {new_status} with {progress}% progress'
        }).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error updating status: {e}")
        return False


def render_compliance_item(item, org_id, key_prefix):
    """Render a single compliance item with update functionality"""
    item_id = item['compliance_item_id']
    item_name = item['compliance_items']['name']
    item_desc = item['compliance_items']['description'] or "No description"
    status = item['status']
    progress = item['progress']
    notes = item.get('notes', '')
    requirement_code = item['compliance_items'].get('requirement_code', '')
    criticality = item['compliance_items'].get('criticality', 'medium')
    
    # Criticality badge
    crit_colors = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }
    crit_badge = crit_colors.get(criticality, '⚪')
    
    with st.container():
        col1, col2, col3 = st.columns([5, 2, 1])
        
        with col1:
            if requirement_code:
                st.markdown(f"### {item_name} `{requirement_code}`")
            else:
                st.markdown(f"### {item_name}")
            st.caption(f"{crit_badge} **{criticality.upper()}** | {item_desc}")
            if notes:
                st.caption(f"📝 *{notes}*")
        
        with col2:
            st.markdown(f"**Progress: {progress}%**")
            st.progress(progress / 100)
        
        with col3:
            if status == 'compliant':
                st.success("**✓ OK**")
            elif status == 'warning':
                st.warning("**⚠ WARN**")
            elif status == 'critical':
                st.error("**❌ CRIT**")
            else:
                st.info("**○ NEW**")
        
        # Action buttons
        bcol1, bcol2, bcol3 = st.columns(3)
        
        with bcol1:
            if st.button("🔄 UPDATE", key=f"{key_prefix}_update_{item_id}", use_container_width=True):
                st.session_state[f'show_modal_{item_id}'] = True
        
        if st.session_state.get(f'show_modal_{item_id}', False):
            with st.form(f"update_form_{item_id}"):
                st.markdown(f"## Update: {item_name}")
                st.markdown("---")
                
                new_status = st.selectbox(
                    "**Status**",
                    ["compliant", "warning", "critical", "not_started"],
                    index=["compliant", "warning", "critical", "not_started"].index(status),
                    key=f"{key_prefix}_status_{item_id}"
                )
                
                new_progress = st.slider("**Progress (%)**", 0, 100, progress, key=f"{key_prefix}_progress_{item_id}")
                
                new_notes = st.text_area("**Notes**", value=notes if notes else '', height=100, key=f"{key_prefix}_notes_{item_id}")
                
                st.markdown("")
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 SAVE CHANGES", use_container_width=True)
                with col2:
                    cancelled = st.form_submit_button("❌ CANCEL", use_container_width=True)
                
                if submitted:
                    if update_compliance_status(item_id, org_id, new_status, new_progress, new_notes):
                        st.success("✅ Status updated successfully!")
                        st.session_state[f'show_modal_{item_id}'] = False
                        st.cache_data.clear()
                        st.rerun()
                
                if cancelled:
                    st.session_state[f'show_modal_{item_id}'] = False
                    st.rerun()
        
        with bcol2:
            if st.button("📤 UPLOAD", key=f"{key_prefix}_upload_{item_id}", use_container_width=True):
                st.info("📁 File upload coming soon...")
        
        with bcol3:
            if st.button("📜 HISTORY", key=f"{key_prefix}_history_{item_id}", use_container_width=True):
                st.info("📊 Audit history coming soon...")
        
        st.markdown("---")


# =============================================================================
# MAIN PAGE
# =============================================================================

st.title("📋 Compliance Frameworks")
st.markdown("### Detailed view of all regulatory requirements")
st.markdown("")

org_id = st.session_state.get('organization_id', '11111111-1111-1111-1111-111111111111')

try:
    compliance_data = get_compliance_data(org_id)
    
    if not compliance_data:
        st.warning("No compliance data found. Make sure you've run the seed data in Supabase.")
        st.stop()
    
except Exception as e:
    st.error(f"Error loading compliance data: {e}")
    st.stop()

# Calculate summary stats
total_items = len(compliance_data)
compliant = len([d for d in compliance_data if d['status'] == 'compliant'])
warning = len([d for d in compliance_data if d['status'] == 'warning'])
critical = len([d for d in compliance_data if d['status'] == 'critical'])

col1, col2, col3, col4 = st.columns(4)
col1.metric("**Total Items**", total_items)
col2.metric("**✅ Compliant**", compliant)
col3.metric("**⚠️ Warning**", warning)
col4.metric("**🔴 Critical**", critical)

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏦 Bank of Ghana",
    "💰 AML/CFT",
    "🔒 Data Protection",
    "💳 Payment Systems",
    "🔐 ISO 27001",
    "💳 PCI DSS"
])

with tab1:
    st.markdown("## 🏦 Bank of Ghana Requirements")
    st.markdown("**Capital adequacy, liquidity, KYC, and transaction monitoring**")
    st.markdown("")
    
    bog_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'bog']
    
    if not bog_items:
        st.info("No Bank of Ghana compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(bog_items)} requirements**")
        st.markdown("")
        
        for item in bog_items:
            render_compliance_item(item, org_id, "bog")

with tab2:
    st.markdown("## 💰 AML/CFT Requirements")
    st.markdown("**Anti-Money Laundering and Counter-Financing of Terrorism**")
    st.markdown("")
    
    aml_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'aml']
    
    if not aml_items:
        st.info("No AML/CFT compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(aml_items)} requirements**")
        st.markdown("")
        
        for item in aml_items:
            render_compliance_item(item, org_id, "aml")

with tab3:
    st.markdown("## 🔒 Data Protection Act Requirements")
    st.markdown("**Data Protection Act 2012 (Act 843)**")
    st.markdown("")
    
    data_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'data']
    
    if not data_items:
        st.info("No Data Protection compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(data_items)} requirements**")
        st.markdown("")
        
        for item in data_items:
            render_compliance_item(item, org_id, "data")

with tab4:
    st.markdown("## 💳 Payment Systems Act Requirements")
    st.markdown("**Payment Systems Act 2003 (Act 662)**")
    st.markdown("")
    
    payment_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'payment']
    
    if not payment_items:
        st.info("No Payment Systems compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(payment_items)} requirements**")
        st.markdown("")
        
        for item in payment_items:
            render_compliance_item(item, org_id, "payment")

with tab5:
    st.markdown("## 🔐 ISO 27001:2022 Requirements")
    st.markdown("**Information Security Management System**")
    st.markdown("")
    
    iso_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'iso']
    
    if not iso_items:
        st.info("No ISO 27001 compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(iso_items)} requirements**")
        st.markdown("")
        
        for item in iso_items:
            render_compliance_item(item, org_id, "iso")

with tab6:
    st.markdown("## 💳 PCI DSS v4.0 Requirements")
    st.markdown("**Payment Card Industry Data Security Standard**")
    st.markdown("")
    
    pci_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'pci']
    
    if not pci_items:
        st.info("No PCI DSS compliance items found.")
    else:
        st.caption(f"📊 Tracking **{len(pci_items)} requirements**")
        st.markdown("")
        
        for item in pci_items:
            render_compliance_item(item, org_id, "pci")

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("← BACK TO DASHBOARD", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("📥 EXPORT REPORT", use_container_width=True):
        st.info("Report export feature coming soon!")

st.markdown("")
st.info("💡 **Tip:** Click 'UPDATE' to change compliance status and add notes for any requirement.")
