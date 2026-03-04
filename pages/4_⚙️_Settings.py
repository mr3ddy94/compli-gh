import streamlit as st
import pandas as pd

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")
st.markdown("Configure your organization and application preferences")

tab1, tab2, tab3, tab4 = st.tabs(["🏢 Organization", "🔔 Notifications", "👥 Team Members", "🔐 Security"])

with tab1:
    st.subheader("Organization Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        org_name = st.text_input(
            "Organization Name",
            value=st.session_state.get('organization_name', 'Demo Fintech Ltd')
        )
        
        license_type = st.selectbox(
            "License Type",
            ["Payment Service Provider", "Mobile Money Operator", "Digital Lender", "Neobank", "Remittance Service"]
        )
        
        registration_number = st.text_input("Company Registration Number", "CS-123456789")
        
        tin_number = st.text_input("TIN Number", "C0012345678")
    
    with col2:
        employees = st.number_input("Number of Employees", min_value=1, value=50, step=1)
        
        establishment_date = st.date_input("Date of Establishment")
        
        regulatory_status = st.selectbox(
            "Regulatory Status",
            ["Fully Licensed", "Provisional License", "Application Pending"]
        )
        
        annual_revenue = st.selectbox(
            "Annual Revenue Range (GHS)",
            ["< 1M", "1M - 5M", "5M - 10M", "10M - 50M", "> 50M"]
        )
    
    st.markdown("---")
    st.subheader("Contact Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        primary_contact = st.text_input("Primary Contact Person", "John Mensah")
        contact_email = st.text_input("Contact Email", "compliance@demo.gh")
    
    with col2:
        contact_phone = st.text_input("Contact Phone", "+233 20 123 4567")
        address = st.text_area("Physical Address", "123 Independence Avenue, Accra, Ghana")
    
    st.markdown("---")
    
    if st.button("💾 Save Organization Settings", use_container_width=True):
        st.session_state.organization_name = org_name
        st.success("✅ Organization settings saved successfully!")

with tab2:
    st.subheader("Notification Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Email Notifications")
        email_enabled = st.checkbox("Enable Email Notifications", value=True)
        
        if email_enabled:
            notification_email = st.text_input("Notification Email", "compliance@demo.gh")
            
            st.markdown("**Notify me about:**")
            notify_compliance = st.checkbox("Compliance status changes", value=True)
            notify_deadlines = st.checkbox("Upcoming deadlines", value=True)
            notify_risk = st.checkbox("Risk level changes", value=True)
            notify_audit = st.checkbox("Audit events", value=True)
            notify_team = st.checkbox("Team activity", value=False)
    
    with col2:
        st.markdown("### Deadline Reminders")
        deadline_reminder = st.slider("Days before deadline to remind", 1, 30, 7)
        
        reminder_frequency = st.selectbox(
            "Reminder Frequency",
            ["Once", "Daily", "Every 3 days", "Weekly"]
        )
        
        st.markdown("### Report Schedule")
        auto_reports = st.checkbox("Enable automatic report generation", value=True)
        
        if auto_reports:
            report_frequency = st.selectbox(
                "Report Frequency",
                ["Weekly", "Monthly", "Quarterly"]
            )
            
            report_day = st.selectbox(
                "Generate on",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "1st of month", "Last day of month"]
            )
    
    st.markdown("---")
    
    if st.button("💾 Save Notification Settings", use_container_width=True):
        st.success("✅ Notification preferences saved!")

with tab3:
    st.subheader("Team Members Management")
    
    # Display current team members
    team_members = pd.DataFrame({
        'Name': ['John Mensah', 'Ama Kwakye', 'Kofi Asante', 'Abena Osei'],
        'Email': ['john@demo.gh', 'ama@demo.gh', 'kofi@demo.gh', 'abena@demo.gh'],
        'Role': ['Admin', 'Compliance Officer', 'Viewer', 'Compliance Officer'],
        'Status': ['Active', 'Active', 'Active', 'Invited'],
        'Last Active': ['2 hours ago', '5 hours ago', '1 day ago', 'Pending']
    })
    
    st.dataframe(team_members, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Add new team member
    st.subheader("➕ Invite Team Member")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_name = st.text_input("Full Name")
    
    with col2:
        new_email = st.text_input("Email Address")
    
    with col3:
        new_role = st.selectbox("Role", ["Admin", "Compliance Officer", "Viewer"])
    
    if st.button("📧 Send Invitation", use_container_width=True):
        if new_name and new_email:
            st.success(f"✅ Invitation sent to {new_name} ({new_email})")
        else:
            st.error("Please fill in all fields")
    
    st.markdown("---")
    
    # Role descriptions
    with st.expander("ℹ️ Role Descriptions"):
        st.markdown("""
        **Admin:**
        - Full access to all features
        - Can manage team members
        - Can change organization settings
        - Can approve compliance status updates
        
        **Compliance Officer:**
        - Update compliance status
        - Upload documents
        - Generate reports
        - View audit trails
        - Cannot manage team or settings
        
        **Viewer:**
        - Read-only access
        - View dashboards and reports
        - Cannot make changes
        - Cannot upload documents
        """)

with tab4:
    st.subheader("Security Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Authentication")
        mfa_enabled = st.checkbox("Enable Two-Factor Authentication (2FA)", value=False)
        
        if mfa_enabled:
            st.info("📱 2FA will be required for all users on next login")
        
        session_timeout = st.slider("Session Timeout (minutes)", 15, 120, 30)
        
        password_expiry = st.selectbox(
            "Password Expiry",
            ["Never", "30 days", "60 days", "90 days", "180 days"]
        )
    
    with col2:
        st.markdown("### Access Control")
        ip_whitelist = st.checkbox("Enable IP Whitelisting", value=False)
        
        if ip_whitelist:
            allowed_ips = st.text_area(
                "Allowed IP Addresses (one per line)",
                "41.189.178.0/24\n102.176.0.0/16"
            )
        
        login_attempts = st.number_input("Max Failed Login Attempts", min_value=3, max_value=10, value=5)
        
        lockout_duration = st.selectbox(
            "Account Lockout Duration",
            ["15 minutes", "30 minutes", "1 hour", "24 hours", "Permanent"]
        )
    
    st.markdown("---")
    
    st.markdown("### Audit & Compliance")
    
    log_retention = st.selectbox(
        "Audit Log Retention Period",
        ["6 months", "1 year", "2 years", "3 years", "5 years", "7 years"]
    )
    
    data_encryption = st.checkbox("Enable End-to-End Encryption", value=True)
    
    st.markdown("---")
    
    if st.button("💾 Save Security Settings", use_container_width=True):
        st.success("✅ Security settings updated!")
    
    st.markdown("---")
    
    # Security status
    st.subheader("🔐 Security Status")
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Security Score", "85/100", "↑ 5")
    col2.metric("Last Security Audit", "14 days ago")
    col3.metric("Active Sessions", "3")

st.markdown("---")

if st.button("← Back to Dashboard", use_container_width=True):
    st.switch_page("app.py")
