import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Risk Assessment", page_icon="⚠️", layout="wide")

st.title("⚠️ Risk Assessment")
st.markdown("Comprehensive risk analysis across all compliance frameworks")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Risk Breakdown by Category")
    
    risk_factors = pd.DataFrame({
        'Category': ['Regulatory Changes', 'Operational Risk', 'Compliance Gaps', 'Market Risk', 'Cybersecurity'],
        'Level': ['Low', 'Medium', 'Low', 'Low', 'Medium'],
        'Score': [15, 35, 20, 10, 28],
        'Impact': ['Minor', 'Moderate', 'Minor', 'Minor', 'Moderate']
    })
    
    st.dataframe(risk_factors, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Priority Mitigation Actions")
    
    st.error("🔴 **HIGH PRIORITY**")
    st.markdown("- Complete ISO 27001 security awareness training (23 employees)")
    st.markdown("- Complete AML/CFT staff training (18 employees)")
    
    st.warning("🟡 **MEDIUM PRIORITY**")
    st.markdown("- Schedule quarterly access rights review (85 accounts)")
    st.markdown("- Complete PCI DSS vulnerability scan (due in 8 days)")
    st.markdown("- Resolve payment disputes beyond SLA (8 cases)")
    
    st.info("🟢 **LOW PRIORITY**")
    st.markdown("- Update data breach response plan")
    st.markdown("- Review PCI DSS security policies (15 policies)")

with col2:
    st.subheader("📈 Risk Trend Analysis")
    
    # Generate 6 months of risk data
    dates = pd.date_range(end=datetime.now(), periods=6, freq='M')
    scores = [45, 42, 38, 35, 33, 32]
    
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
    mcol1.metric("Current Score", "32", "-13 pts (6mo)")
    mcol2.metric("Target Score", "30", "2 pts to go")
    mcol3.metric("Improvement", "29%", "↓ Since start")

st.markdown("---")

# Risk matrix
st.subheader("🎯 Risk Matrix by Framework")

frameworks_risk = pd.DataFrame({
    'Framework': ['Bank of Ghana', 'AML/CFT', 'Data Protection', 'Payment Systems', 'ISO 27001', 'PCI DSS'],
    'Likelihood': ['Low', 'Medium', 'Low', 'Low', 'Medium', 'Low'],
    'Impact': ['High', 'High', 'Medium', 'Medium', 'High', 'Medium'],
    'Overall Risk': ['Medium', 'High', 'Low', 'Low', 'High', 'Medium'],
    'Mitigation Status': ['In Progress', 'Action Needed', 'On Track', 'On Track', 'Action Needed', 'In Progress']
})

# Color code based on risk level
def color_risk(val):
    if val == 'High':
        return 'background-color: #DC2626; color: white'
    elif val == 'Medium':
        return 'background-color: #F59E0B; color: white'
    else:
        return 'background-color: #10B981; color: white'

st.dataframe(
    frameworks_risk.style.applymap(color_risk, subset=['Overall Risk']),
    use_container_width=True,
    hide_index=True
)

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
