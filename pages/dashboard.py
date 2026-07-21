"""Auto-generated interactive dashboard."""
from __future__ import annotations
import streamlit as st
from components.ui import section_header, card
from analytics.kpis import generate_kpis, format_kpi
from analytics.insights import generate_insights
from charts.engine import auto_generate_charts, render_chart_grid
from database.db import db
from utils.logger import log


def render() -> None:
    section_header("AI Dashboard", "📊")
    df = st.session_state.get("df")
    profile = st.session_state.get("profile")
    if df is None or profile is None:
        st.warning("⚠️ Please upload a dataset first from the Home page.")
        return

    # Filters sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Filters")
        filters = {}
        for col in profile.categorical_cols[:5]:
            options = st.multiselect(col, df[col].dropna().unique().tolist()[:50])
            if options:
                filters[col] = options
        for col in profile.numeric_cols[:3]:
            mn, mx = float(df[col].min()), float(df[col].max())
            if mn != mx:
                rng = st.slider(col, mn, mx, (mn, mx))
                filters[col] = rng
        if st.button("🔄 Reset Filters"):
            st.session_state["filters"] = {}
            st.rerun()

    # Apply filters
    filtered = df.copy()
    for col, val in filters.items():
        try:
            if isinstance(val, list):
                filtered = filtered[filtered[col].isin(val)]
            elif isinstance(val, tuple):
                filtered = filtered[(filtered[col] >= val[0]) & (filtered[col] <= val[1])]
        except Exception as e:
            log.warning(f"Filter on {col} failed: {e}")

    # KPIs
    kpis = generate_kpis(filtered, profile)
    kpi_items = list(kpis.items())[:8]
    cols = st.columns(min(4, len(kpi_items)))
    for i, (k, v) in enumerate(kpi_items):
        with cols[i % 4]:
            st.markdown(card(k, format_kpi(v), "", f"#{['7C3AED','4F46E5','06B6D4','10B981','F59E0B','EF4444'][i%6]}"),
                        unsafe_allow_html=True)

    st.markdown("---")

    # Charts
    charts = auto_generate_charts(filtered, profile, max_charts=10)
    render_chart_grid(charts, cols=2)

    # Insights panel
    st.markdown("---")
    section_header("AI Insights", "🤖")
    insights = generate_insights(filtered, profile)
    sev_colors = {"info": "#06B6D4", "warning": "#F59E0B", "danger": "#EF4444"}
    for ins in insights:
        st.markdown(f"""
        <div class='glass' style='border-left:4px solid {sev_colors.get(ins['severity'],'#06B6D4')}; margin:8px 0; padding:14px;'>
          <div style='display:flex; justify-content:space-between;'>
            <b>{ins['title']}</b>
            <span style='color:var(--muted); font-size:11px;'>{ins['category']} · {ins['confidence']*100:.0f}%</span>
          </div>
          <div style='color:var(--muted); margin-top:6px; font-size:13px;'>{ins['body']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Save dashboard
    st.markdown("---")
    name = st.text_input("Dashboard name", value=st.session_state.get("active_dashboard", "Default"))
    if st.button("💾 Save Dashboard"):
        try:
            db.save_dashboard(st.session_state["username"], name,
                              {"filters": filters, "kpis": list(kpis.keys())})
            db.audit(st.session_state["username"], "save_dashboard", name)
            st.success(f"✅ Saved as '{name}'")
        except Exception as e:
            st.error(f"Save failed: {e}")

    # List saved dashboards
    saved = db.list_dashboards(st.session_state["username"])
    if saved:
        st.markdown("**Saved dashboards:**")
        for s in saved:
            st.markdown(f"- {s['name']} _(updated {s['updated_at'][:19]})_")