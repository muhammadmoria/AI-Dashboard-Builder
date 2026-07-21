"""User settings & system info."""
from __future__ import annotations
import streamlit as st
from components.ui import section_header
from database.db import db
from config.settings import settings


def render() -> None:
    section_header("Settings", "⚙️")
    st.markdown(f"### Welcome, **{st.session_state.get('name', 'User')}**")
    st.markdown(f"**Username:** `{st.session_state.get('username', '')}`")

    st.markdown("### 🎨 Appearance")
    theme = st.radio("Theme", ["Dark", "Light"], index=0 if st.session_state.get("theme") == "dark" else 1)
    st.session_state["theme"] = theme.lower()
    if st.button("Apply Theme"): st.rerun()

    st.markdown("### 📦 Saved Dashboards")
    saved = db.list_dashboards(st.session_state.get("username", "guest"))
    for s in saved:
        cols = st.columns([3, 1, 1])
        with cols[0]: st.write(s["name"])
        with cols[1]: st.write(s["updated_at"][:10])
        with cols[2]:
            if st.button("🗑", key=f"del_{s['name']}"):
                db.delete_dashboard(st.session_state["username"], s["name"])
                st.rerun()

    st.markdown("### 🛡️ Audit Log")
    try:
        with db.conn() as c:
            rows = c.execute("SELECT action, resource, timestamp FROM audit_log WHERE username=? ORDER BY timestamp DESC LIMIT 20",
                             (st.session_state.get("username", "guest"),)).fetchall()
        for r in rows:
            st.markdown(f"- `{r['timestamp'][:19]}` · **{r['action']}** · {r['resource']}")
    except Exception:
        st.info("No audit logs available.")

    st.markdown("### ℹ️ System Info")
    st.json({"version": settings.APP_VERSION, "max_upload_mb": settings.MAX_UPLOAD_MB,
             "openai_enabled": settings.ENABLE_OPENAI})