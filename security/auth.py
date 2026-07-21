"""Authentication using streamlit-authenticator with secure hashing."""
from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import yaml
from config.settings import settings
from database.db import db
from utils.logger import log

CRED_FILE = settings.ROOT / "config" / "credentials.yaml"


def _load_config() -> dict:
    """Load or initialize the credentials YAML file safely."""
    if not CRED_FILE.exists():
        CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
        cfg = {
            "credentials": {"usernames": {}},
            "cookie": {
                "name": "nexus_cookie", 
                "key": settings.JWT_SECRET,
                "expiry_days": settings.COOKIE_EXPIRY_DAYS
            },
            "preauthorized": {"emails": []}
        }
        with open(CRED_FILE, "w") as f:
            yaml.safe_dump(cfg, f)
        return cfg
    
    with open(CRED_FILE, "r") as f:
        cfg = yaml.safe_load(f)
    
    # Fallback if file is empty or corrupted
    if not cfg or "credentials" not in cfg:
        cfg = {
            "credentials": {"usernames": {}},
            "cookie": {
                "name": "nexus_cookie", 
                "key": settings.JWT_SECRET,
                "expiry_days": settings.COOKIE_EXPIRY_DAYS
            },
            "preauthorized": {"emails": []}
        }
        
    return cfg


def init_authenticator():
    """Initialize the authenticator with the correct parameters."""
    # Cache the config in session state to preserve in-memory updates (like new registrations)
    if "auth_cfg" not in st.session_state:
        st.session_state["auth_cfg"] = _load_config()
    
    cfg = st.session_state["auth_cfg"]
    
    authenticator = stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie"]["name"],
        cfg["cookie"]["key"],
        cfg["cookie"]["expiry_days"],
        cfg.get("preauthorized", {"emails": []})
    )
    return authenticator


def render_auth_ui(authenticator) -> None:
    auth_container = st.container()
    with auth_container:
        # 0.3.x API: location is the first argument
        name, auth_status, username = authenticator.login(location='main')
        
        if auth_status is False:
            st.error("❌ Username/password is incorrect")
        elif auth_status is None:
            st.info("🔐 Please enter your credentials")
            with st.expander("Don't have an account? Register"):
                try:
                    # 0.3.x API: pre_authorization is a keyword argument
                    if authenticator.register_user(location='main', pre_authorization=False):
                        _persist_credentials()
                        st.success("✅ Registration successful — please log in.")
                        st.rerun()
                except Exception as e:
                    log.error(f"Registration error: {e}")
                    st.error(f"Registration failed: {e}")
        elif auth_status:
            st.session_state["username"] = username
            st.session_state["name"] = name
            with st.sidebar:
                # 0.3.x API: button_name and location are keyword arguments
                authenticator.logout(button_name='Logout', location='sidebar')


def _persist_credentials() -> None:
    """Save the updated session state config back to the YAML file."""
    cfg = st.session_state.get("auth_cfg")
    if cfg:
        with open(CRED_FILE, "w") as f:
            yaml.safe_dump(cfg, f, default_flow_style=False)


def require_auth() -> bool:
    return bool(st.session_state.get("authentication_status"))