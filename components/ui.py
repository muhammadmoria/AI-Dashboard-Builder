"""Reusable UI primitives & global CSS injection."""
from __future__ import annotations
import streamlit as st
from pathlib import Path
from config.settings import settings


def inject_global_css() -> None:
    css_path = settings.ASSETS_DIR / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    # Theme variables
    theme = st.session_state.get("theme", "dark")
    theme_vars = """
    :root {
      --bg: #0B1020; --bg-2: #131A33; --card: rgba(255,255,255,0.04);
      --border: rgba(255,255,255,0.08); --text: #E5E7EB; --muted: #9CA3AF;
      --accent: #7C3AED; --accent-2: #4F46E5; --success:#10B981;
      --warning:#F59E0B; --danger:#EF4444;
    }
    """ if theme == "dark" else """
    :root {
      --bg:#F5F7FB; --bg-2:#FFFFFF; --card: rgba(255,255,255,0.85);
      --border: rgba(15,23,42,0.08); --text:#0F172A; --muted:#64748B;
      --accent:#7C3AED; --accent-2:#4F46E5; --success:#10B981;
      --warning:#F59E0B; --danger:#EF4444;
    }
    """
    st.markdown(f"<style>{theme_vars}{css}</style>", unsafe_allow_html=True)


def render_sidebar_theme_toggle() -> None:
    with st.sidebar:
        theme = st.selectbox("🎨 Theme", ["dark", "light"],
                             index=0 if st.session_state.get("theme") == "dark" else 1)
        if theme != st.session_state.get("theme"):
            st.session_state["theme"] = theme
            st.rerun()


def card(title: str, value: str, subtitle: str = "", color: str = "var(--accent)") -> str:
    return f"""
    <div class="metric-card" style="--accent:{color}">
      <div class="metric-title">{title}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-subtitle">{subtitle}</div>
    </div>
    """


def glass_container(content: str) -> None:
    st.markdown(f'<div class="glass">{content}</div>', unsafe_allow_html=True)


def section_header(title: str, icon: str = "✨") -> None:
    st.markdown(f"""
    <div class="section-header">
      <span class="section-icon">{icon}</span>
      <h2>{title}</h2>
    </div>
    """, unsafe_allow_html=True)


def hero() -> None:
    st.markdown("""
    <div class="hero">
      <div class="hero-badge">⚡ Enterprise AI Analytics</div>
      <h1 class="hero-title">Turn Raw Data Into <span class="gradient-text">Decisions</span></h1>
      <p class="hero-subtitle">Upload a dataset and let AI build your dashboards,
         surface insights, train models, and generate reports — in seconds.</p>
    </div>
    """, unsafe_allow_html=True)