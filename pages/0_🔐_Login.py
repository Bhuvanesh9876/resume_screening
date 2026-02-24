import streamlit as st
from supabase_client import supabase
from utils.auth_manager import save_session
from utils.remember_email import save_remembered_email, get_remembered_email, clear_remembered_email

try:
    st.set_page_config(page_title="Login", layout="centered")
except Exception:
    pass

st.title("🔐 Login")

if "user" in st.session_state:
    user = st.session_state["user"]
    email = getattr(user, "email", None) or getattr(user, "id", "User")
    st.success(f"Welcome back, {email}!")
    if st.button("🚀 Go to Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📄_Recruiter_Input.py")
    st.stop()

if supabase is None:
    st.info("Supabase is not configured. You can continue as a guest.")
    if st.button("🚀 Continue as Guest", use_container_width=True, type="primary"):
        class GuestUser:
            id = "guest"
            email = "guest@local"
        st.session_state["user"] = GuestUser()
        st.switch_page("pages/1_📄_Recruiter_Input.py")
    st.stop()

if "show_signin_after_signup" not in st.session_state:
    st.session_state.show_signin_after_signup = False

tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

with tab1:
    st.subheader("Sign In")

    # Get remembered email if available
    remembered_email = get_remembered_email()
    
    email = st.text_input("Email", value=remembered_email, key="signin_email")
    password = st.text_input("Password", type="password", key="signin_pwd")
    
    # Remember me checkbox (default checked if there's a remembered email)
    remember_me = st.checkbox("Remember my email", value=bool(remembered_email))

    if st.button("Login"):
        if not email or not password:
            st.warning("Please enter email and password.")
        else:
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                # Save or clear email based on remember_me checkbox
                if remember_me:
                    save_remembered_email(email)
                else:
                    clear_remembered_email()
                
                save_session(res)
                st.success("Login successful")
                st.switch_page("pages/1_📄_Recruiter_Input.py")

            except Exception:
                st.error("Invalid email or password.")

with tab2:
    st.subheader("Sign Up")

    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pwd")
    confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

    if st.button("Create Account"):
        if not email or not password or not confirm:
            st.warning("All fields are required.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        elif password != confirm:
            st.warning("Passwords do not match.")
        else:
            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })

                # Save the email for convenience when signing in
                save_remembered_email(email)

                st.success("Account created successfully.")
                st.info("You can now sign in with your credentials.")

                st.session_state.show_signin_after_signup = True

            except Exception as e:
                msg = str(e).lower()
                if "already registered" in msg:
                    st.warning("This email is already registered. Please sign in.")
                elif "password" in msg:
                    st.warning("Password must be at least 6 characters.")
                else:
                    st.error("Signup failed. Please try again.")

    if st.session_state.show_signin_after_signup:
        st.divider()
        if st.button("➡️ Go to Sign In"):
            st.session_state.show_signin_after_signup = False
            st.rerun()
