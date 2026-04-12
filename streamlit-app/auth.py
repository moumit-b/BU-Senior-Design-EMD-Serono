"""
Authentication Module

Simple login/logout for the research platform.
All team members share admin/admin during development.
"""

import hashlib
import streamlit as st
from typing import Optional, Dict, Any


def _hash_password(password: str) -> str:
    """SHA-256 hash (dev-grade; admin/admin credentials are shared by design)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_default_users(db_manager) -> None:
    """
    Seed the default admin user on first run.
    Safe to call on every startup — no-op if user already exists.
    """
    try:
        from context.db_models import UserRecord
        with db_manager.get_session() as session:
            existing = session.query(UserRecord).filter_by(username="admin").first()
            if existing is None:
                admin = UserRecord(
                    username="admin",
                    password_hash=_hash_password("admin"),
                    display_name="Admin",
                    is_active=True,
                )
                session.add(admin)
    except Exception as e:
        # Don't crash if DB is not yet ready
        print(f"[auth] init_default_users warning: {e}")


def verify_credentials(db_manager, username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify username and password.

    Returns a dict with user info on success, None on failure.
    """
    try:
        from context.db_models import UserRecord
        with db_manager.get_session() as session:
            user = session.query(UserRecord).filter_by(
                username=username.strip().lower(),
                is_active=True,
            ).first()
            if user and user.password_hash == _hash_password(password):
                return {
                    "user_id": user.user_id,
                    "username": user.username,
                    "display_name": user.display_name or user.username,
                }
    except Exception as e:
        print(f"[auth] verify_credentials error: {e}")
    return None


def render_login_page(db_manager) -> None:
    """
    Render the login page. On success, sets session state and triggers a rerun.
    This should be called at the top of main() before any other UI is rendered.
    """
    # Center the login form with custom CSS
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: #0f1117;
        }
        .login-container {
            max-width: 420px;
            margin: 80px auto 0;
            padding: 2.5rem 2rem;
            background: #1a1d27;
            border: 1px solid #2d3148;
            border-radius: 12px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .login-header h1 {
            font-size: 1.6rem;
            font-weight: 700;
            color: #e2e8f0;
            margin: 0;
        }
        .login-header p {
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 0.3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Narrow centered column
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        st.markdown("---")
        st.markdown("## Pharma Research Intelligence")
        st.markdown("##### EMD Serono · Research Platform")
        st.markdown("---")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = verify_credentials(db_manager, username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = user
                    st.session_state["user_id"] = user["user_id"]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

        st.markdown(
            "<div style='text-align:center;color:#475569;font-size:0.75rem;margin-top:1rem'>"
            "Pharma Research Intelligence Platform"
            "</div>",
            unsafe_allow_html=True,
        )


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the currently authenticated user dict, or None."""
    return st.session_state.get("current_user")


def logout() -> None:
    """Clear all auth-related session state."""
    keys_to_clear = [
        "authenticated", "current_user", "user_id",
        "current_chat_session_id", "messages",
        "identified_drug", "drug_msg_count", "generated_report",
        "report_dev_log",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
