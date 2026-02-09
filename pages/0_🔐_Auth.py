import streamlit as st
from supabase_client import supabase
from utils.auth_manager import save_session

st.set_page_config(page_title="Authentication", layout="centered")

st.title("🔐 Authentication")

tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

with tab1:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            save_session(res)
            st.switch_page("app.py")
        except Exception as e:
            st.error(str(e))

with tab2:
    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_pwd")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if password != confirm:
            st.error("Passwords do not match")
        else:
            supabase.auth.sign_up({"email": email, "password": password})
            st.success("Account created. Please sign in.")
