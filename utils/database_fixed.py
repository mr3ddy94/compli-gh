import streamlit as st

st.set_page_config(page_title="Database Diagnostic", page_icon="🔧", layout="wide")

st.title("🔧 Database Connection Diagnostic")
st.markdown("This tool helps identify and fix database connection issues.")

# =============================================================================
# TEST 1: CHECK IF SECRETS EXIST
# =============================================================================

st.header("1️⃣ Check Secrets Configuration")

if "supabase" in st.secrets:
    st.success("✅ Supabase secrets found!")
    
    # Check URL
    if "url" in st.secrets["supabase"]:
        url = st.secrets["supabase"]["url"]
        st.success(f"✅ URL configured: `{url[:30]}...`")
        
        # Validate URL format
        if url.startswith("https://") and "supabase.co" in url:
            st.success("✅ URL format looks correct")
        else:
            st.error("❌ URL format looks wrong. Should be: https://xxxxx.supabase.co")
    else:
        st.error("❌ URL missing in secrets")
    
    # Check Key
    if "key" in st.secrets["supabase"]:
        key = st.secrets["supabase"]["key"]
        st.success(f"✅ API Key configured: `{key[:20]}...`")
        
        # Validate key format
        if key.startswith("eyJ"):
            st.success("✅ API Key format looks correct (JWT token)")
        else:
            st.warning("⚠️ API Key format unusual. Should start with 'eyJ'")
    else:
        st.error("❌ API Key missing in secrets")
        
else:
    st.error("❌ Supabase secrets NOT found!")
    st.info("""
    **To add secrets:**
    1. Go to: https://share.streamlit.io
    2. Click your app → Settings (⋮) → Secrets
    3. Add:
    ```toml
    [supabase]
    url = "https://your-project.supabase.co"
    key = "your-anon-public-key"
    ```
    4. Click Save
    5. Reboot app
    """)
    st.stop()

st.markdown("---")

# =============================================================================
# TEST 2: TRY TO CONNECT
# =============================================================================

st.header("2️⃣ Test Database Connection")

try:
    from supabase import create_client
    
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    
    st.info("Attempting to create Supabase client...")
    
    supabase = create_client(url, key)
    
    st.success("✅ Supabase client created successfully!")
    
except Exception as e:
    st.error(f"❌ Failed to create Supabase client: {e}")
    st.info("Check that your URL and Key are correct in Supabase dashboard")
    st.stop()

st.markdown("---")

# =============================================================================
# TEST 3: CHECK TABLE ACCESS
# =============================================================================

st.header("3️⃣ Test Table Access")

tables_to_check = [
    'organizations',
    'users', 
    'frameworks',
    'compliance_items',
    'compliance_status',
    'audit_logs',
    'documents'
]

results = []

for table in tables_to_check:
    try:
        response = supabase.table(table).select('id').limit(1).execute()
        row_count_response = supabase.table(table).select('id', count='exact').execute()
        row_count = row_count_response.count if row_count_response.count else 0
        
        results.append({
            'Table': table,
            'Status': '✅ Accessible',
            'Rows': row_count,
            'Issue': 'None'
        })
    except Exception as e:
        error_msg = str(e)
        
        if "permission denied" in error_msg.lower():
            issue = "RLS Blocking"
        elif "does not exist" in error_msg.lower():
            issue = "Table Missing"
        else:
            issue = error_msg[:50]
        
        results.append({
            'Table': table,
            'Status': '❌ Error',
            'Rows': 0,
            'Issue': issue
        })

import pandas as pd
df = pd.DataFrame(results)

st.dataframe(df, use_container_width=True, hide_index=True)

# Count issues
error_count = len([r for r in results if r['Status'] == '❌ Error'])
empty_count = len([r for r in results if r['Status'] == '✅ Accessible' and r['Rows'] == 0])

if error_count > 0:
    st.error(f"❌ {error_count} table(s) have access errors!")
    st.warning("**Most likely cause:** Row Level Security (RLS) is blocking access")
    
    st.info("""
    **To fix RLS issues:**
    1. Go to Supabase SQL Editor
    2. Run this SQL:
    
    ```sql
    -- Disable RLS on all tables
    ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
    ALTER TABLE users DISABLE ROW LEVEL SECURITY;
    ALTER TABLE frameworks DISABLE ROW LEVEL SECURITY;
    ALTER TABLE compliance_items DISABLE ROW LEVEL SECURITY;
    ALTER TABLE compliance_status DISABLE ROW LEVEL SECURITY;
    ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
    ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
    ```
    
    3. Reboot your Streamlit app
    """)

if empty_count > 0:
    st.warning(f"⚠️ {empty_count} table(s) are empty!")
    st.info("Tables exist but have no data. You need to run the seed data SQL.")

if error_count == 0 and empty_count == 0:
    st.success("🎉 All tables are accessible and have data!")

st.markdown("---")

# =============================================================================
# TEST 4: DETAILED TABLE INSPECTION
# =============================================================================

st.header("4️⃣ Detailed Table Inspection")

selected_table = st.selectbox("Select table to inspect:", tables_to_check)

if st.button(f"Inspect {selected_table}"):
    try:
        response = supabase.table(selected_table).select('*').limit(5).execute()
        
        if response.data:
            st.success(f"✅ Found {len(response.data)} rows (showing first 5)")
            
            # Convert to dataframe for display
            df_inspect = pd.DataFrame(response.data)
            st.dataframe(df_inspect, use_container_width=True)
        else:
            st.warning(f"⚠️ Table '{selected_table}' is empty")
            st.info("You need to populate this table with seed data")
            
    except Exception as e:
        st.error(f"❌ Error reading {selected_table}: {e}")

st.markdown("---")

# =============================================================================
# TEST 5: SPECIFIC QUERY TESTS
# =============================================================================

st.header("5️⃣ Specific Query Tests")

st.subheader("Test: Fetch Demo Organization")

try:
    org_response = supabase.table('organizations').select('*').eq(
        'id', '11111111-1111-1111-1111-111111111111'
    ).execute()
    
    if org_response.data:
        st.success("✅ Demo organization found!")
        st.json(org_response.data[0])
    else:
        st.error("❌ Demo organization NOT found!")
        st.warning("You need to insert the demo organization with ID: 11111111-1111-1111-1111-111111111111")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.markdown("---")

st.subheader("Test: Fetch Compliance Data")

try:
    comp_response = supabase.table('compliance_status').select(
        '*, compliance_items(name)'
    ).limit(3).execute()
    
    if comp_response.data:
        st.success(f"✅ Found {len(comp_response.data)} compliance records")
        st.json(comp_response.data)
    else:
        st.error("❌ No compliance status data found!")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.markdown("---")

# =============================================================================
# SOLUTIONS
# =============================================================================

st.header("🔧 Common Issues & Solutions")

with st.expander("❌ Permission Denied / RLS Blocking"):
    st.markdown("""
    **Issue:** Row Level Security is blocking the anon key from accessing data.
    
    **Solution:**
    1. Go to Supabase → SQL Editor
    2. Run:
    ```sql
    ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
    ALTER TABLE users DISABLE ROW LEVEL SECURITY;
    ALTER TABLE frameworks DISABLE ROW LEVEL SECURITY;
    ALTER TABLE compliance_items DISABLE ROW LEVEL SECURITY;
    ALTER TABLE compliance_status DISABLE ROW LEVEL SECURITY;
    ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
    ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
    ```
    3. Reboot Streamlit app
    """)

with st.expander("⚠️ Tables Are Empty"):
    st.markdown("""
    **Issue:** Tables exist but have no data.
    
    **Solution:**
    1. Go to Supabase → SQL Editor
    2. Run the complete seed data SQL (see database_complete_fix.md)
    3. Verify data with: `SELECT COUNT(*) FROM organizations;`
    4. Reboot Streamlit app
    """)

with st.expander("❌ Table Does Not Exist"):
    st.markdown("""
    **Issue:** Database tables haven't been created yet.
    
    **Solution:**
    1. Go to Supabase → SQL Editor
    2. Run the CREATE TABLE statements from the SQL file
    3. Then run the INSERT statements
    4. Reboot Streamlit app
    """)

with st.expander("❌ Wrong API Key"):
    st.markdown("""
    **Issue:** Using wrong key type (service_role instead of anon).
    
    **Solution:**
    1. Go to Supabase → Settings → API
    2. Copy the **anon public** key (NOT service_role)
    3. Update Streamlit secrets with the anon key
    4. Reboot Streamlit app
    """)

st.markdown("---")

# =============================================================================
# FINAL STATUS
# =============================================================================

st.header("📊 Final Status")

if error_count == 0 and empty_count == 0:
    st.success("✅ **DATABASE FULLY OPERATIONAL**")
    st.balloons()
    st.info("Your database is properly configured. The main app should work now!")
elif error_count > 0:
    st.error("❌ **DATABASE HAS ACCESS ISSUES**")
    st.warning("Fix RLS policies using the SQL commands above")
elif empty_count > 0:
    st.warning("⚠️ **DATABASE NEEDS DATA**")
    st.info("Run the seed data SQL to populate tables")

st.markdown("---")
st.caption("Database Diagnostic Tool v1.0 | CompliGH")
