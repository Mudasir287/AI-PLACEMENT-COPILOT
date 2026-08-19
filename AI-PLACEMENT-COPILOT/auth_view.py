import streamlit as st
from database import register_user, verify_user


def init_auth_session():
    """Initializes authentication state flags in Streamlit session memory."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None


def render_auth_view():
    """Renders the Login and Registration container."""
    init_auth_session()

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="color: #0ea5e9; margin-bottom: 0;">🚀 AI Placement Co-Pilot</h1>
            <p style="color: #64748b; font-size: 1.1rem;">ATS Optimization, Resume Tailoring & AI Mock Interviews</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register New Account"])

        # --- Login Tab ---
        with tab_login:
            st.subheader("Welcome Back")
            with st.form("login_form"):
                login_username = st.text_input("Username", key="login_user").strip()
                login_password = st.text_input("Password", type="password", key="login_pass")
                submit_login = st.form_submit_button("Log In", use_container_width=True)

                if submit_login:
                    if not login_username or not login_password:
                        st.error("Please enter both username and password.")
                    else:
                        is_valid, user_id = verify_user(login_username, login_password)
                        if is_valid:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_id
                            st.session_state["username"] = login_username
                            st.success(f"Welcome back, {login_username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        # --- Register Tab ---
        with tab_register:
            st.subheader("Create Your Profile")
            with st.form("register_form"):
                reg_username = st.text_input("Choose Username", key="reg_user").strip()
                reg_password = st.text_input("Choose Password", type="password", key="reg_pass")
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                submit_register = st.form_submit_button("Register Account", use_container_width=True)

                if submit_register:
                    if not reg_username or not reg_password:
                        st.error("All fields are required.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    elif len(reg_password) < 6:
                        st.warning("Password must be at least 6 characters long.")
                    else:
                        success, message = register_user(reg_username, reg_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)


def render_user_sidebar():
    """Displays active user information and a logout button in the sidebar."""
    if st.session_state.get("authenticated", False):
        st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.get('username', 'User')}**")
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_id"] = None
            st.session_state["username"] = None
            st.rerun()


# --- Standalone Test Runner for Day 10 ---
if __name__ == "__main__":
    st.set_page_config(page_title="AI Placement Co-Pilot - Auth", page_icon="🔐", layout="wide")
    init_auth_session()

    if not st.session_state["authenticated"]:
        render_auth_view()
    else:
        render_user_sidebar()
        st.title(f"🎉 Access Granted! Welcome, {st.session_state['username']}")
        st.info("Authentication pipeline validated. You are logged in with session persistence.")
