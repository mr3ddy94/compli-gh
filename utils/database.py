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
