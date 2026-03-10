"""
Database connection helper for CompliGH
Manages Supabase client connection and caching
"""

import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Create and cache Supabase client connection
    
    Returns:
        Client: Authenticated Supabase client
    """
    try:
        # Check if secrets exist
        if "supabase" not in st.secrets:
            st.error("⚠️ Supabase configuration not found in secrets!")
            st.info("""
            **To fix this:**
            1. Go to Streamlit Cloud: https://share.streamlit.io
            2. Click your app → Settings (⋮) → Secrets
            3. Add your Supabase credentials:
            
            ```toml
            [supabase]
            url = "https://your-project.supabase.co"
            key = "your-anon-key"
            ```
            """)
            st.stop()
        
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        
        # Validate URL format
        if not supabase_url.startswith("https://"):
            st.error("❌ Invalid Supabase URL format. Must start with https://")
            st.stop()
        
        # Create client
        client = create_client(supabase_url, supabase_key)
        
        # Test connection
        try:
            test_response = client.table('organizations').select('id').limit(1).execute()
            return client
        except Exception as test_error:
            st.error(f"❌ Database connection test failed: {test_error}")
            st.info("""
            **Possible issues:**
            - Check your Supabase URL is correct
            - Check your API key is the 'anon public' key
            - Make sure your database tables exist
            - Check if Row Level Security (RLS) is blocking access
            """)
            st.stop()
            
    except KeyError as e:
        st.error(f"⚠️ Missing Supabase credential: {e}")
        st.info("""
        **Your secrets should look like:**
        ```toml
        [supabase]
        url = "https://xxxxx.supabase.co"
        key = "eyJxxxxx..."
        ```
        """)
        st.stop()
    except Exception as e:
        st.error(f"❌ Unexpected error connecting to database: {e}")
        st.stop()


def test_connection():
    """Test database connection"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('organizations').select('*').limit(1).execute()
        return True
    except Exception as e:
        st.error(f"Connection test failed: {e}")
        return False


def check_rls_policies():
    """Check if RLS is blocking access"""
    try:
        supabase = get_supabase_client()
        
        # Try to read from each table
        tables = ['organizations', 'frameworks', 'compliance_items', 'compliance_status']
        results = {}
        
        for table in tables:
            try:
                response = supabase.table(table).select('id').limit(1).execute()
                results[table] = f"✅ OK ({len(response.data)} rows)"
            except Exception as e:
                results[table] = f"❌ Error: {str(e)[:50]}"
        
        return results
    except:
        return {}
import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase_client():
    """Get Supabase client"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)
