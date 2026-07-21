"""Data profiling, cleaning & exploration."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from components.ui import section_header, card
from analytics.profiler import profile_dataset
from analytics.cleaner import OPERATIONS, undo_last
from utils.logger import log


def render() -> None:
    section_header("Data Studio", "🔬")
    df = st.session_state.get("df")
    if df is None:
        st.warning("⚠️ Upload data first.")
        return
    profile = st.session_state["profile"]

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile", "🧹 Cleaning", "🔎 Explore", "📊 Stats"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Rows", f"{profile.rows:,}")
        with c2: st.metric("Columns", profile.cols)
        with c3: st.metric("Duplicates", profile.duplicate_rows)
        with c4: st.metric("Quality", f"{profile.quality_score:.1f}%")

        st.markdown("### Column Metadata")
        meta_df = pd.DataFrame(profile.columns)
        st.dataframe(meta_df, use_container_width=True, height=400)

        if profile.issues:
            st.markdown("### ⚠️ Detected Issues")
            for issue in profile.issues:
                st.markdown(f"- {issue}")

    with tab2:
        st.markdown("### One-Click Cleaning")
        ops = st.multiselect("Select operations", list(OPERATIONS.keys()),
                             default=list(OPERATIONS.keys())[:2])
        if st.button("🧹 Run Cleaning"):
            try:
                df_clean = st.session_state["df_original"].copy()
                for op_name in ops:
                    df_clean = OPERATIONS[op_name](df_clean)
                st.session_state["df"] = df_clean
                st.session_state["profile"] = profile_dataset(df_clean)
                st.success(f"✅ Applied {len(ops)} operations. Shape: {df_clean.shape}")
                st.rerun()
            except Exception as e:
                st.error(f"Cleaning failed: {e}")

        if st.button("↩️ Undo Last Operation"):
            st.session_state["df"] = undo_last(st.session_state["df"])
            st.session_state["profile"] = profile_dataset(st.session_state["df"])
            st.rerun()

        if st.button("🔄 Reset to Original"):
            st.session_state["df"] = st.session_state["df_original"].copy()
            st.session_state["profile"] = profile_dataset(st.session_state["df"])
            st.rerun()

        st.markdown("**History:**")
        for h in st.session_state.get("cleaning_history", []):
            st.markdown(f"- {h.get('op', 'unknown')}")

    with tab3:
        st.markdown("### Data Explorer")
        gb = GridOptionsBuilder.from_dataframe(df.head(1000))
        gb.configure_default_column(filter=True, sortable=True, resizable=True)
        gb.configure_grid_options(domLayout="autoHeight")
        AgGrid(df.head(1000), gridOptions=gb.build(), theme="streamlit", height=400)

        # Search
        search = st.text_input("🔍 Search across all text columns")
        if search:
            mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
            st.dataframe(df[mask].head(500), use_container_width=True)

    with tab4:
        st.markdown("### Statistical Summary")
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            stats = numeric.describe().T
            stats["skew"] = numeric.skew()
            stats["kurtosis"] = numeric.kurtosis()
            st.dataframe(stats.round(3), use_container_width=True)

            st.markdown("### Correlation Matrix")
            import plotly.express as px
            # FIX: Changed zmid=0 to color_continuous_midpoint=0
            fig = px.imshow(numeric.corr(), color_continuous_scale="RdBu", color_continuous_midpoint=0)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns for statistical summary.")