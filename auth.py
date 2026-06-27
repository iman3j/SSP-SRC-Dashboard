# auth.py — Simple login system

import streamlit as st
import hashlib

USERS = {
    "iman.ahmed": {
        "password": "123456789",
        "name":     "Administrator",
        "role":     "admin",
    },
}

def check_login(username: str, password: str) -> bool:
    user = USERS.get(username.strip().lower())
    return user and password == user["password"]

def get_user(username: str) -> dict:
    return USERS.get(username.strip().lower(), {})

def render_login_page() -> bool:
    st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    </style>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#161b22,#1c2333);border:1px solid #30363d;
        border-radius:16px;padding:40px 36px;text-align:center;margin-top:80px'>
            <div style='font-size:2rem'>⚡</div>
            <div style='font-size:1.2rem;font-weight:600;color:#e6edf3'>SRC Portfolio Dashboard</div>
            <div style='font-size:0.78rem;color:#8b949e;margin-bottom:20px'>Electric Utility · SRC Recovery Monitor</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            username  = st.text_input("👤 Username", placeholder="Enter username")
            password  = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login →", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("⚠️ Username aur password dono required hain.")
                elif check_login(username, password):
                    user = get_user(username)
                    st.session_state["logged_in"] = True
                    st.session_state["username"]  = username.strip().lower()
                    st.session_state["user_name"] = user["name"]
                    st.session_state["user_role"] = user["role"]
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

    return st.session_state.get("logged_in", False)

def logout() -> None:
    for key in ["logged_in", "username", "user_name", "user_role"]:
        st.session_state.pop(key, None)
    st.rerun()

def require_login() -> bool:
    if not st.session_state.get("logged_in", False):
        render_login_page()
        return False
    return True