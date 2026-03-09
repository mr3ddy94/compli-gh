import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_supabase_client

st.set_page_config(page_title="Compliance Frameworks", page_icon="📋", layout="wide")

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
    
    # Fetch frameworks for each item
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
        # Update compliance status
        update_data = {
            'status': new_status,
            'progress': progress,
            'notes': notes,
            'last_updated_at': datetime.now().isoformat()
        }
        
        supabase.table('compliance_status').update(update_data).eq(
            'compliance_item_id', item_id
        ).eq('organization_id', org_id).execute()
        
        # Log the action
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
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show requirement code if available
            if requirement_code:
                st.markdown(f"**{item_name}** `{requirement_code}`")
            else:
                st.markdown(f"**{item_name}**")
            st.caption(f"{item_desc}")
            if notes:
                st.caption(f"📝 *{notes}*")
        
        with col2:
            if status == 'compliant':
                st.success("✓ Compliant")
            elif status == 'warning':
                st.warning("⚠ Action Needed")
            elif status == 'critical':
                st.error("❌ Critical")
            else:
                st.info("○ Not Started")
        
        st.progress(progress / 100)
        st.caption(f"{progress}% complete")
        
        # Action buttons
        bcol1, bcol2, bcol3 = st.columns(3)
        
        with bcol1:
            if st.button("🔄 Update Status", key=f"{key_prefix}_update_{item_id}", use_container_width=True):
                st.session_state[f'show_modal_{item_id}'] = True
        
        # Show update modal if button clicked
        if st.session_state.get(f'show_modal_{item_id}', False):
            with st.form(f"update_form_{item_id}"):
                st.markdown(f"### Update: {item_name}")
                
                new_status = st.selectbox(
                    "Status",
                    ["compliant", "warning", "critical", "not_started"],
                    index=["compliant", "warning", "critical", "not_started"].index(status),
                    key=f"{key_prefix}_status_{item_id}"
                )
                
                new_progress = st.slider("Progress (%)", 0, 100, progress, key=f"{key_prefix}_progress_{item_id}")
                
                new_notes = st.text_area("Notes", value=notes if notes else '', key=f"{key_prefix}_notes_{item_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with col2:
                    cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                
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
            if st.button("📤 Upload Evidence", key=f"{key_prefix}_upload_{item_id}", use_container_width=True):
                st.info("📁 File upload coming soon...")
        
        with bcol3:
            if st.button("📜 View History", key=f"{key_prefix}_history_{item_id}", use_container_width=True):
                st.info("📊 Audit history coming soon...")
        
        st.markdown("---")


# =============================================================================
# MAIN PAGE
# =============================================================================

st.title("📋 Compliance Frameworks")
st.markdown("Detailed view of all regulatory requirements")

# Get organization ID
org_id = st.session_state.get('organization_id', '11111111-1111-1111-1111-111111111111')

# Fetch compliance data
try:
    compliance_data = get_compliance_data(org_id)
    
    if not compliance_data:
        st.warning("No compliance data found. Make sure you've run the seed data in Supabase.")
        st.stop()
    
except Exception as e:
    st.error(f"Error loading compliance data: {e}")
    st.stop()

# Tabs for different frameworks
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏦 Bank of Ghana",
    "💰 AML/CFT",
    "🔒 Data Protection",
    "💳 Payment Systems",
    "🔐 ISO 27001",
    "💳 PCI DSS"
])

# =============================================================================
# TAB 1: BANK OF GHANA
# =============================================================================

with tab1:
    st.subheader("Bank of Ghana Requirements")
    st.markdown("Capital adequacy, liquidity, KYC, and transaction monitoring requirements")
    st.markdown("")
    
    # Filter for Bank of Ghana items
    bog_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'bog']
    
    if not bog_items:
        st.info("No Bank of Ghana compliance items found.")
    else:
        st.caption(f"Tracking {len(bog_items)} requirements")
        st.markdown("")
        
        for item in bog_items:
            render_compliance_item(item, org_id, "bog")

# =============================================================================
# TAB 2: AML/CFT
# =============================================================================

with tab2:
    st.subheader("💰 AML/CFT Requirements")
    st.markdown("Anti-Money Laundering and Counter-Financing of Terrorism")
    st.markdown("")
    
    aml_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'aml']
    
    if not aml_items:
        st.info("No AML/CFT compliance items found.")
    else:
        st.caption(f"Tracking {len(aml_items)} requirements")
        st.markdown("")
        
        for item in aml_items:
            render_compliance_item(item, org_id, "aml")

# =============================================================================
# TAB 3: DATA PROTECTION
# =============================================================================

with tab3:
    st.subheader("🔒 Data Protection Act Requirements")
    st.markdown("Data Protection Act 2012 (Act 843)")
    st.markdown("")
    
    data_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'data']
    
    if not data_items:
        st.info("No Data Protection compliance items found.")
    else:
        st.caption(f"Tracking {len(data_items)} requirements")
        st.markdown("")
        
        for item in data_items:
            render_compliance_item(item, org_id, "data")

# =============================================================================
# TAB 4: PAYMENT SYSTEMS
# =============================================================================

with tab4:
    st.subheader("💳 Payment Systems Act Requirements")
    st.markdown("Payment Systems Act 2003 (Act 662)")
    st.markdown("")
    
    payment_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'payment']
    
    if not payment_items:
        st.info("No Payment Systems compliance items found.")
    else:
        st.caption(f"Tracking {len(payment_items)} requirements")
        st.markdown("")
        
        for item in payment_items:
            render_compliance_item(item, org_id, "payment")

# =============================================================================
# TAB 5: ISO 27001
# =============================================================================

with tab5:
    st.subheader("🔐 ISO 27001:2022 Requirements")
    st.markdown("Information Security Management System")
    st.markdown("")
    
    iso_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'iso']
    
    if not iso_items:
        st.info("No ISO 27001 compliance items found.")
    else:
        st.caption(f"Tracking {len(iso_items)} requirements")
        st.markdown("")
        
        for item in iso_items:
            render_compliance_item(item, org_id, "iso")

# =============================================================================
# TAB 6: PCI DSS
# =============================================================================

with tab6:
    st.subheader("💳 PCI DSS v4.0 Requirements")
    st.markdown("Payment Card Industry Data Security Standard")
    st.markdown("")
    
    pci_items = [item for item in compliance_data if item.get('framework') and item['framework']['short_code'] == 'pci']
    
    if not pci_items:
        st.info("No PCI DSS compliance items found.")
    else:
        st.caption(f"Tracking {len(pci_items)} requirements")
        st.markdown("")
        
        for item in pci_items:
            render_compliance_item(item, org_id, "pci")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("← Back to Dashboard", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("📥 Export Compliance Report", use_container_width=True):
        st.info("Report export feature coming soon!")

st.markdown("")
st.caption("💡 **Tip:** Click 'Update Status' to change compliance status and add notes for any requirement.")
