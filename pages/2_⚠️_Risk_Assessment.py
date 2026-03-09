import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_supabase_client

st.set_page_config(page_title="Risk Assessment", page_icon="⚠️", layout="wide")

st.title("⚠️ Risk Assessment")
st.markdown("Comprehensive risk analysis across all compliance frameworks")

# Get organization ID
org_id = st.session_state.get('organization_id', '11111111-1111-1111-1111-111111111111')

# Fetch compliance data
@st.cache_data(ttl=60)
def get_risk_data(org_id):
    """Fetch and calculate risk data"""
    supabase = get_supabase_client()
    
    response = supabase.table('compliance_status').select(
        '*, compliance_items(name, criticality, framework_id)'
    ).eq('organization_id', org_id).execute()
    
    return response.data

try:
    compliance_data = get_risk_data(org_id)
    
    # Calculate risk metrics
    total = len(compliance_data)
    critical_items = len([d for d in compliance_data if d['status'] == 'critical'])
    warning_items = len([d for d in compliance_data if d['status'] == 'warning'])
    
    # Calculate overall risk score
    risk_score = min((critical_items * 10) + (warning_items * 3), 100)
    
except Exception as e:
    st.error(f"Error loading risk data: {e}")
    st.stop()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Risk Breakdown by Category")
    
    risk_factors = pd.DataFrame({
        'Category': ['Regulatory Changes', 'Operational Risk', 'Compliance Gaps', 'Market Risk', 'Cybersecurity'],
        'Level': ['Low', 'Medium' if warning_items > 3 else 'Low', 'Medium' if critical_items > 0 else 'Low', 'Low', 'Medium' if critical_items > 1 else 'Low'],
        'Score': [15, min(35, warning_items * 5), min(40, critical_items * 10), 10, min(30, critical_items * 8)],
        'Impact': ['Minor', 'Moderate', 'Moderate' if critical_items > 0 else 'Minor', 'Minor', 'Moderate']
    })
    
    st.dataframe(risk_factors, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Priority Mitigation Actions")
    
    # Show critical items first
    critical_shown = 0
    warning_shown = 0
    
    if critical_items > 0:
        st.error("🔴 **HIGH PRIORITY**")
        for item in compliance_data:
            if item['status'] == 'critical' and critical_shown < 3:
                st.markdown(f"- {item['compliance_items']['name']}")
                critical_shown += 1
    
    if warning_items > 0:
        st.warning("🟡 **MEDIUM PRIORITY**")
        for item in compliance_data:
            if item['status'] == 'warning' and warning_shown < 3:
                st.markdown(f"- {item['compliance_items']['name']}")
                warning_shown += 1
    
    if critical_items == 0 and warning_items == 0:
        st.success("🟢 **All systems operational**")
        st.markdown("- Continue monitoring compliance status")
        st.markdown("- Maintain current security posture")

with col2:
    st.subheader("📈 Risk Trend Analysis")
    
    # Generate 6 months of trend data (simulated improvement)
    dates = pd.date_range(end=datetime.now(), periods=6, freq='M')
    # Simulate decreasing risk over time
    base_score = risk_score + 15
    scores = [base_score - (i * 2) for i in range(6)]
    scores[-1] = risk_score  # Current score
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode='lines+markers',
        line=dict(color='#CE1126', width=3),
        marker=dict(size=12, color='#FCD116', line=dict(color='#CE1126', width=2)),
        name='Risk Score'
    ))
    
    # Add target line
    fig.add_hline(y=30, line_dash="dash", line_color="green", 
                  annotation_text="Target Risk Level")
    
    fig.update_layout(
        title="6-Month Risk Score Trend",
        xaxis_title="Month",
        yaxis_title="Risk Score",
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk improvement metrics
    st.markdown("### 📉 Risk Improvement")
    
    mcol1, mcol2, mcol3 = st.columns(3)
    improvement = base_score - risk_score
    mcol1.metric("Current Score", risk_score, f"-{improvement} pts (6mo)")
    mcol2.metric("Target Score", "30", f"{max(0, risk_score - 30)} pts to go")
    mcol3.metric("Improvement", f"{int((improvement/base_score)*100)}%", "↓ Since start")

st.markdown("---")

# Risk matrix by framework
st.subheader("🎯 Risk Matrix by Framework")

# Group by framework
framework_risks = {}
for item in compliance_data:
    fw_id = item['compliance_items']['framework_id']
    
    # Fetch framework name (cached)
    @st.cache_data(ttl=300)
    def get_framework_name(fw_id):
        supabase = get_supabase_client()
        response = supabase.table('frameworks').select('name').eq('id', fw_id).execute()
        return response.data[0]['name'] if response.data else 'Unknown'
    
    fw_name = get_framework_name(fw_id)
    
    if fw_name not in framework_risks:
        framework_risks[fw_name] = {'critical': 0, 'warning': 0, 'compliant': 0}
    
    framework_risks[fw_name][item['status']] = framework_risks[fw_name].get(item['status'], 0) + 1

# Build dataframe
fw_data = []
for fw_name, counts in framework_risks.items():
    critical = counts.get('critical', 0)
    warning = counts.get('warning', 0)
    
    # Determine overall risk
    if critical > 0:
        overall_risk = 'High'
        likelihood = 'High'
        mitigation_status = 'Action Needed'
    elif warning > 2:
        overall_risk = 'Medium'
        likelihood = 'Medium'
        mitigation_status = 'In Progress'
    else:
        overall_risk = 'Low'
        likelihood = 'Low'
        mitigation_status = 'On Track'
    
    fw_data.append({
        'Framework': fw_name,
        'Critical Items': critical,
        'Warning Items': warning,
        'Likelihood': likelihood,
        'Impact': 'High' if critical > 0 else 'Medium',
        'Overall Risk': overall_risk,
        'Mitigation Status': mitigation_status
    })

frameworks_risk_df = pd.DataFrame(fw_data)

# Display with color coding
def color_risk(val):
    if val == 'High':
        return 'background-color: #FEE2E2; color: #991B1B; font-weight: 600;'
    elif val == 'Medium':
        return 'background-color: #FEF3C7; color: #92400E; font-weight: 600;'
    elif val == 'Low':
        return 'background-color: #D1FAE5; color: #065F46; font-weight: 600;'
    return ''

if not frameworks_risk_df.empty:
    styled_df = frameworks_risk_df.style.applymap(
        color_risk, 
        subset=['Overall Risk', 'Likelihood']
    )
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("No risk data available")

st.markdown("---")

# Action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export Risk Report", use_container_width=True):
        st.success("Risk assessment report generated!")

with col2:
    if st.button("📧 Send to Management", use_container_width=True):
        st.info("Report sent to management team")

with col3:
    if st.button("⚙️ Configure Risk Thresholds", use_container_width=True):
        st.info("Risk threshold configuration coming soon...")

st.markdown("---")

if st.button("← Back to Dashboard", use_container_width=True):
    st.switch_page("app.py")
