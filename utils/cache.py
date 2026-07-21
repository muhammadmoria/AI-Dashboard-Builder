"""Session state initialization & helpers."""
from __future__ import annotations
import streamlit as st
import pandas as pd


def init_session_state(post_auth: bool = False) -> None:
    defaults = {
        "df": None,
        "df_original": None,
        "profile": None,
        "cleaning_history": [],
        "dashboards": {},
        "active_dashboard": "Default",
        "theme": "dark",
        "last_upload": None,
        "filters": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if post_auth and "user_dashboards" not in st.session_state:
        st.session_state["user_dashboards"] = {}


def reset_data() -> None:
    st.session_state["df"] = None
    st.session_state["df_original"] = None
    st.session_state["profile"] = None
    st.session_state["cleaning_history"] = []
    st.session_state["filters"] = {}