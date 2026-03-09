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
        
    Note:
        Uses Streamlit secrets for credentials
        Connection is cached across app reruns
    """
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        
        client = create_client(supabase_url, supabase_key)
        return client
    except KeyError:
        st.error("⚠️ Supabase credentials not found in secrets. Please configure in Streamlit Cloud settings.")
        st.info("""
        **To add secrets:**
        1. Go to Streamlit Cloud dashboard
        2. Click your app → Settings → Secrets
        3. Add:
        ```
        [supabase]
        url = "your-supabase-url"
        key = "your-anon-key"
        ```
        """)
        st.stop()
    except Exception as e:
        st.error(f"❌ Error connecting to database: {e}")
        st.stop()


def test_connection():
    """
    Test database connection by fetching organizations
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('organizations').select('*').limit(1).execute()
        return True
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return False


def get_table_count(table_name: str) -> int:
    """
    Get row count for a table
    
    Args:
        table_name: Name of the table
        
    Returns:
        int: Number of rows in table
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table(table_name).select('id', count='exact').execute()
        return response.count
    except:
        return 0
