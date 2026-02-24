from supabase import create_client
import streamlit as st

supabase = None
try:
    if "SUPABASE_URL" in st.secrets and "SUPABASE_ANON_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        supabase = create_client(url, key)
except Exception:
    supabase = None
