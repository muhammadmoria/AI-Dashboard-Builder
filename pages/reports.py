"""Report generation & export center."""
from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
from components.ui import section_header
from reports.pdf import generate_pdf_report
from exports.exporters import to_csv, to_excel, to_json, to_html_dashboard
from analytics.kpis import generate_kpis
from analytics.insights import generate_insights
from charts.engine import auto_generate_charts
from utils.logger import log


def render() -> None:
    section_header("Reports & Exports", "📄")
    df = st.session_state.get("df")
    profile = st.session_state.get("profile")
    if df is None or profile is None:
        st.warning("⚠️ Upload data first.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📕 PDF Executive Report")
        if st.button("Generate PDF Report"):
            try:
                with st.spinner("Building premium PDF..."):
                    pdf_bytes = generate_pdf_report(df, profile,
                                                    st.session_state.get("username", "analyst"))
                st.download_button("📥 Download PDF", pdf_bytes,
                                   file_name=f"nexus_report_{profile.rows}rows.pdf",
                                   mime="application/pdf")
                st.success("✅ Premium PDF ready!")
            except Exception as e:
                log.error(f"PDF generation failed: {e}", exc_info=True)
                st.error(f"Failed: {e}")

    with c2:
        st.markdown("### 📊 Data Exports")
        c_csv, c_xlsx, c_json = st.columns(3)
        with c_csv:
            if st.button("Export CSV"): st.download_button("Download", to_csv(df), "data.csv", "text/csv")
        with c_xlsx:
            if st.button("Export Excel"): st.download_button("Download", to_excel(df), "data.xlsx",
                                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c_json:
            if st.button("Export JSON"): st.download_button("Download", to_json(df), "data.json", "application/json")

    st.markdown("---")
    
    # HTML Preview & Download
    st.markdown("### 🌐 Premium HTML Dashboard")
    if st.button("👁️ Generate & Preview HTML Dashboard"):
        try:
            with st.spinner("Generating beautiful HTML dashboard..."):
                charts = auto_generate_charts(df, profile, max_charts=6)
                kpis = generate_kpis(df, profile)
                insights = generate_insights(df, profile)
                html = to_html_dashboard(df, profile, charts, kpis, insights)
                st.session_state["html_preview"] = html
        except Exception as e:
            st.error(f"HTML export failed: {e}")

    # Show Preview if generated
    if "html_preview" in st.session_state:
        html = st.session_state["html_preview"]
        st.download_button("📥 Download HTML File", html.encode("utf-8"),
                           file_name="nexus_dashboard.html", mime="text/html")
        st.markdown("#### Live Preview:")
        components.html(html, height=1000, scrolling=True)