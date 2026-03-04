import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Audit Trail", page_icon="📜", layout="wide")

st.title("📜 Audit Trail")
st.markdown("Complete activity log for all compliance actions")

# Filters
st.markdown("### 🔍 Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))

with col2:
    date_to = st.date_input("To Date", datetime.now())

with col3:
    action_type = st.selectbox(
        "Action Type",
        ["All", "UPDATE", "FLAG", "GENERATE", "DELETE", "COMPLETE", "UPLOAD", "REVIEW"]
    )

with col4:
    category = st.selectbox(
        "Category",
        ["All", "CDD", "AML", "REPORT", "DATA", "TRAINING", "ISO", "PCI", "BoG"]
    )

st.markdown("---")

# Sample audit logs
logs = pd.DataFrame({
    'Timestamp': [
        '2026-03-04 14:23:15',
        '2026-03-04 13:45:32',
        '2026-03-04 12:18:45',
        '2026-03-04 11:02:19',
        '2026-03-04 09:30:44',
        '2026-03-03 16:15:22',
        '2026-03-03 14:42:11',
        '2026-03-03 11:20:33',
        '2026-03-02 15:55:12',
        '2026-03-02 10:30:45',
        '2026-03-01 16:45:22',
        '2026-03-01 13:20:15',
        '2026-03-01 09:15:44',
        '2026-02-28 14:30:22',
        '2026-02-28 11:45:11'
    ],
    'User': [
        'John Mensah', 'Ama Kwakye', 'System', 'Kofi Asante', 
        'John Mensah', 'Ama Kwakye', 'John Mensah', 'Kofi Asante',
        'System', 'Ama Kwakye', 'John Mensah', 'Kofi Asante',
        'Ama Kwakye', 'John Mensah', 'System'
    ],
    'Action': [
        'UPDATE', 'FLAG', 'GENERATE', 'DELETE', 'COMPLETE',
        'UPLOAD', 'REVIEW', 'UPDATE', 'GENERATE', 'FLAG',
        'UPLOAD', 'COMPLETE', 'REVIEW', 'UPDATE', 'GENERATE'
    ],
    'Category': [
        'CDD', 'AML', 'REPORT', 'DATA', 'TRAINING',
        'ISO', 'PCI', 'BoG', 'REPORT', 'AML',
        'DATA', 'TRAINING', 'PCI', 'CDD', 'REPORT'
    ],
    'Description': [
        'Updated customer verification status for Account #GH-45823',
        'Flagged suspicious transaction: GHS 45,000 cross-border transfer',
        'Generated monthly compliance report for February 2026',
        'Processed 15 customer data deletion requests',
        '18 employees completed AML refresher course',
        'Uploaded ISO 27001 security policy v2.1 document',
        'Reviewed PCI DSS firewall configuration',
        'Updated Bank of Ghana capital adequacy report',
        'Auto-generated quarterly compliance summary',
        'Flagged 3 transactions for enhanced due diligence',
        'Uploaded data breach response procedure v3.0',
        '25 staff members completed ISO security awareness training',
        'Reviewed and approved PCI vulnerability scan results',
        'Updated 42 customer KYC profiles',
        'Generated annual DPC compliance report'
    ],
    'IP Address': [
        '41.189.178.24', '41.189.178.25', '10.0.0.1', '41.189.178.26',
        '41.189.178.24', '41.189.178.25', '41.189.178.24', '41.189.178.26',
        '10.0.0.1', '41.189.178.25', '41.189.178.24', '41.189.178.26',
        '41.189.178.25', '41.189.178.24', '10.0.0.1'
    ]
})

# Display logs
st.subheader(f"📊 Showing {len(logs)} audit entries")

# Make it interactive with colors for different action types
def highlight_action(row):
    action_colors = {
        'UPDATE': 'background-color: #3B82F6; color: white',
        'FLAG': 'background-color: #F59E0B; color: white',
        'GENERATE': 'background-color: #10B981; color: white',
        'DELETE': 'background-color: #DC2626; color: white',
        'COMPLETE': 'background-color: #8B5CF6; color: white',
        'UPLOAD': 'background-color: #06B6D4; color: white',
        'REVIEW': 'background-color: #EC4899; color: white'
    }
    return [action_colors.get(row['Action'], '')] * len(row)

styled_logs = logs.style.apply(highlight_action, axis=1, subset=['Action'])

st.dataframe(styled_logs, use_container_width=True, hide_index=True, height=500)

st.markdown("---")

# Summary statistics
st.subheader("📈 Activity Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Actions", len(logs))
col2.metric("Unique Users", logs['User'].nunique())
col3.metric("Categories", logs['Category'].nunique())
col4.metric("Today's Actions", len(logs[logs['Timestamp'].str.contains('2026-03-04')]))

st.markdown("---")

# Export options
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export to CSV", use_container_width=True):
        csv = logs.to_csv(index=False)
        st.download_button(
            label="Download CSV File",
            data=csv,
            file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    if st.button("📧 Email Report", use_container_width=True):
        st.info("Audit trail report sent to compliance@demo.gh")

with col3:
    if st.button("🔍 Advanced Search", use_container_width=True):
        st.info("Advanced search feature coming soon...")

st.markdown("---")

if st.button("← Back to Dashboard", use_container_width=True):
    st.switch_page("app.py")
