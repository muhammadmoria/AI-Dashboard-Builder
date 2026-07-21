"""Landing page — hero, upload, recent activity."""
from __future__ import annotations
import streamlit as st
from pathlib import Path
import pandas as pd
from components.ui import hero, card, section_header, glass_container
from utils.io import validate_file, load_dataset
from utils.logger import log
from analytics.profiler import profile_dataset
from database.db import db  # <--- Moved import to the top!


def render() -> None:
    hero()

    # Upload zone
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded = st.file_uploader(
            "📤 Upload your dataset",
            type=["csv", "xlsx", "xls", "json", "parquet", "tsv", "feather", "zip"],
            accept_multiple_files=False,
            help=f"Max {500}MB. We auto-detect encoding & schema."
        )
        if uploaded:
            try:
                validate_file(uploaded.name, uploaded.size)
                tmp = Path("cache/uploads") / uploaded.name
                tmp.parent.mkdir(parents=True, exist_ok=True)
                with open(tmp, "wb") as f:
                    f.write(uploaded.getbuffer())
                with st.spinner("🔍 Analyzing your data..."):
                    df = load_dataset(tmp)
                    st.session_state["df"] = df
                    st.session_state["df_original"] = df.copy()
                    st.session_state["profile"] = profile_dataset(df)
                    st.session_state["last_upload"] = uploaded.name
                    db.record_upload(st.session_state.get("username", "guest"),
                                     uploaded.name, len(df), len(df.columns))
                    db.audit(st.session_state.get("username", "guest"), "upload", uploaded.name)
                st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
                st.balloons()
            except Exception as e:
                log.error(f"Upload failed: {e}", exc_info=True)
                st.error(f"❌ Upload failed: {str(e)[:200]}")

    # Feature cards
    section_header("Capabilities", "🚀")
    features = [
        ("🤖", "AI Insights", "Automatic business insights, anomaly detection & trend analysis."),
        ("📊", "Auto Visualizations", "Smart chart selection based on data types & relationships."),
        ("🧠", "ML Lab", "Train classification, regression & clustering models in one click."),
        ("📄", "PDF Reports", "Premium executive reports with KPIs, charts & recommendations."),
        ("🧹", "Data Cleaning", "Missing values, outliers, types & duplicates — handled."),
        ("🔐", "Enterprise Security", "Auth, audit logs, input validation & secure sessions."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="feature-card">
              <div class="feature-icon">{icon}</div>
              <div class="feature-title">{title}</div>
              <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # Quick stats
    if st.session_state.get("profile"):
        section_header("Dataset Overview", "📈")
        p = st.session_state["profile"]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(card("Rows", f"{p.rows:,}", "Total records", "#7C3AED"), unsafe_allow_html=True)
        with c2: st.markdown(card("Columns", str(p.cols), "Data dimensions", "#4F46E5"), unsafe_allow_html=True)
        with c3: st.markdown(card("Quality", f"{p.quality_score:.1f}%", "Health score", "#10B981"), unsafe_allow_html=True)
        with c4: st.markdown(card("Memory", f"{p.memory_mb:.1f}MB", "In-memory size", "#06B6D4"), unsafe_allow_html=True)

    # Recent uploads (from DB)
    section_header("Recent Activity", "🕐")
    try:
        username = st.session_state.get("username", "guest")
        with db.conn() as c:
            rows = c.execute("SELECT filename, rows, cols, timestamp FROM uploads WHERE username=? ORDER BY timestamp DESC LIMIT 5",
                             (username,)).fetchall()
        if rows:
            for r in rows:
                st.markdown(f"""
                <div class='glass' style='padding:10px 14px; margin:6px 0;'>
                  📄 <b>{r['filename']}</b> · {r['rows']:,} rows × {r['cols']} cols
                  <span style='color:var(--muted); float:right'>{r['timestamp'][:19]}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent uploads yet.")
    except Exception as e:
        st.info("Activity tracking unavailable.")