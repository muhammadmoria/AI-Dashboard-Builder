"""Enterprise AI Dashboard Builder — Application Entry Point."""
from __future__ import annotations
import streamlit as st
from pathlib import Path
import sys

# Ensure project root importable
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from utils.logger import log
from components.ui import inject_global_css, render_sidebar_theme_toggle, glass_container
from security.auth import init_authenticator, require_auth, render_auth_ui
from utils.cache import init_session_state
from pages import home, dashboard, data_studio, ml_lab, reports, settings as settings_page
from streamlit_option_menu import option_menu


def main() -> None:
    st.set_page_config(
        page_title="Nexus BI — AI Dashboard Builder",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_css()
    init_session_state()

    authenticator = init_authenticator()
    render_auth_ui(authenticator)

    if not require_auth():
        return

    render_sidebar_theme_toggle()
    init_session_state(post_auth=True)

    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        selected = option_menu(
            menu_title=None,
            options=["Home", "Dashboard", "Data Studio", "ML Lab", "Reports", "Settings"],
            icons=["house", "speedometer2", "database", "cpu", "file-earmark-text", "gear"],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#7C3AED", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "4px 0",
                    "padding": "10px 14px",
                    "border-radius": "10px",
                    "color": "var(--text)",
                    "background-color": "transparent",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg,#7C3AED,#4F46E5)",
                    "color": "white",
                    "font-weight": "600",
                },
            },
        )

        st.divider()
        if st.session_state.get("df") is not None:
            st.success(f"📊 {st.session_state['df'].shape[0]:,} rows loaded")
        else:
            st.info("📤 Upload data to begin")

    pages = {
        "Home": home.render,
        "Dashboard": dashboard.render,
        "Data Studio": data_studio.render,
        "ML Lab": ml_lab.render,
        "Reports": reports.render,
        "Settings": settings_page.render,
    }
    try:
        pages[selected]()
    except Exception as e:
        log.error("Page render failed", exc_info=True)
        st.error(f"⚠️ Something went wrong: {str(e)[:200]}")
        with st.expander("🔍 Technical details"):
            st.exception(e)


if __name__ == "__main__":
    main()