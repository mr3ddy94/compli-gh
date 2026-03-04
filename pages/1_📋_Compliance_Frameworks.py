import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compliance Frameworks", page_icon="📋", layout="wide")

st.title("📋 Compliance Frameworks")
st.markdown("Detailed view of all regulatory requirements")

# Tabs for different frameworks
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏦 Bank of Ghana",
    "💰 AML/CFT",
    "🔒 Data Protection",
    "💳 Payment Systems",
    "🔐 ISO 27001",
    "💳 PCI DSS"
])

with tab1:
    st.subheader("Bank of Ghana Requirements")
    
    items = [
        {"name": "Capital Adequacy Requirements", "status": "compliant", "progress": 100, 
         "details": "Minimum capital: GHS 10M | Current: GHS 15M"},
        {"name": "Customer Due Diligence (CDD)", "status": "warning", "progress": 78, 
         "details": "125 customer profiles require enhanced verification"},
        {"name": "Transaction Monitoring", "status": "compliant", "progress": 100, 
         "details": "Real-time monitoring active for all transactions"},
        {"name": "Liquidity Requirements", "status": "compliant", "progress": 100, 
         "details": "Liquidity ratio: 25% (Required: 20%)"}
    ]
    
    for item in items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                elif item['status'] == 'warning':
                    st.warning("⚠ Action Needed")
                else:
                    st.error("❌ Critical")
            
            st.progress(item['progress'] / 100)
            
            # Action buttons
            bcol1, bcol2, bcol3 = st.columns(3)
            with bcol1:
                if st.button("Update Status", key=f"update_{item['name']}"):
                    st.info("Status update modal coming soon...")
            with bcol2:
                if st.button("Upload Evidence", key=f"upload_{item['name']}"):
                    st.info("File upload coming soon...")
            with bcol3:
                if st.button("View History", key=f"history_{item['name']}"):
                    st.info("Audit history coming soon...")
            
            st.markdown("---")

with tab2:
    st.subheader("💰 AML/CFT Requirements")
    
    aml_items = [
        {"name": "Suspicious Transaction Reporting", "status": "compliant", "progress": 100,
         "details": "All STRs reported to FIC within 24 hours"},
        {"name": "PEP Screening", "status": "warning", "progress": 65,
         "details": "42 PEP accounts due for annual review"},
        {"name": "Record Keeping", "status": "compliant", "progress": 100,
         "details": "All records maintained for 6+ years"},
        {"name": "Staff AML Training", "status": "critical", "progress": 45,
         "details": "Annual training overdue for 18 employees"}
    ]
    
    for item in aml_items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                elif item['status'] == 'warning':
                    st.warning("⚠ Review Needed")
                else:
                    st.error("❌ Overdue")
            
            st.progress(item['progress'] / 100)
            st.markdown("---")

with tab3:
    st.subheader("🔒 Data Protection Act Requirements")
    
    data_items = [
        {"name": "DPC Registration", "status": "compliant", "progress": 100,
         "details": "Registered with Data Protection Commission"},
        {"name": "Consent Management", "status": "compliant", "progress": 100,
         "details": "Customer consent obtained and documented"},
        {"name": "Data Breach Response Plan", "status": "warning", "progress": 70,
         "details": "Annual review and testing needed"},
        {"name": "Data Retention Policy", "status": "compliant", "progress": 100,
         "details": "Automated deletion after retention period"}
    ]
    
    for item in data_items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                else:
                    st.warning("⚠ Update Required")
            
            st.progress(item['progress'] / 100)
            st.markdown("---")

with tab4:
    st.subheader("💳 Payment Systems Act Requirements")
    
    payment_items = [
        {"name": "PSP Licensing", "status": "compliant", "progress": 100,
         "details": "Licensed as Payment Service Provider by BoG"},
        {"name": "Transaction Limits", "status": "compliant", "progress": 100,
         "details": "All transactions within regulatory limits"},
        {"name": "Payment Dispute Resolution", "status": "warning", "progress": 82,
         "details": "8 disputes pending beyond 14-day SLA"},
        {"name": "E-money Float Management", "status": "compliant", "progress": 100,
         "details": "Customer funds properly segregated"}
    ]
    
    for item in payment_items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                else:
                    st.warning("⚠ Attention Needed")
            
            st.progress(item['progress'] / 100)
            st.markdown("---")

with tab5:
    st.subheader("🔐 ISO 27001:2022 Requirements")
    
    iso_items = [
        {"name": "Information Security Policy (A.5.1)", "status": "compliant", "progress": 100,
         "details": "Security policy documented and communicated"},
        {"name": "Access Control Management (A.9)", "status": "warning", "progress": 72,
         "details": "Quarterly access review due - 85 accounts"},
        {"name": "Cryptographic Controls (A.10)", "status": "compliant", "progress": 100,
         "details": "TLS 1.3 and AES-256 encryption implemented"},
        {"name": "Vulnerability Management (A.12.6)", "status": "warning", "progress": 68,
         "details": "12 medium-risk vulnerabilities identified"},
        {"name": "Business Continuity (A.17)", "status": "compliant", "progress": 100,
         "details": "BCP/DRP tested - RTO: 4h, RPO: 1h"},
        {"name": "Security Awareness Training (A.7.2.2)", "status": "critical", "progress": 35,
         "details": "Annual training overdue for 23 employees"}
    ]
    
    for item in iso_items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                elif item['status'] == 'warning':
                    st.warning("⚠ Review Required")
                else:
                    st.error("❌ Overdue")
            
            st.progress(item['progress'] / 100)
            st.markdown("---")

with tab6:
    st.subheader("💳 PCI DSS v4.0 Requirements")
    
    pci_items = [
        {"name": "Requirement 1: Firewall Configuration", "status": "compliant", "progress": 100,
         "details": "Network segmentation and quarterly reviews"},
        {"name": "Requirement 3: Protect Cardholder Data", "status": "compliant", "progress": 100,
         "details": "PAN truncation, masking, and tokenization"},
        {"name": "Requirement 8: Access Control", "status": "compliant", "progress": 100,
         "details": "MFA enabled, unique IDs, RBAC implemented"},
        {"name": "Requirement 10: Monitoring & Logging", "status": "compliant", "progress": 100,
         "details": "24/7 monitoring, 12-month log retention"},
        {"name": "Requirement 11: Vulnerability Scanning", "status": "warning", "progress": 75,
         "details": "Quarterly ASV scan due in 8 days"},
        {"name": "Requirement 12: Security Policy", "status": "warning", "progress": 80,
         "details": "Annual policy review - 15 policies need updates"}
    ]
    
    for item in pci_items:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['details'])
            with col2:
                if item['status'] == 'compliant':
                    st.success("✓ Compliant")
                else:
                    st.warning("⚠ Action Required")
            
            st.progress(item['progress'] / 100)
            st.markdown("---")

# Back to dashboard button
st.markdown("---")
if st.button("← Back to Dashboard", use_container_width=True):
    st.switch_page("app.py")
