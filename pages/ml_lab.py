"""Machine Learning experimentation lab."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.ui import section_header, card
from ml.modeler import train_models, cluster_data, detect_task
from utils.logger import log


def render() -> None:
    section_header("ML Lab", "🧠")
    df = st.session_state.get("df")
    profile = st.session_state.get("profile")
    if df is None or profile is None:
        st.warning("⚠️ Upload data first.")
        return

    tab1, tab2 = st.tabs(["🎯 Supervised", "🔍 Unsupervised"])

    with tab1:
        st.markdown("### Train Models")
        target = st.selectbox("Target variable",
                              profile.numeric_cols + profile.categorical_cols + profile.boolean_cols,
                              index=profile.numeric_cols.index(profile.target_suggestion)
                              if profile.target_suggestion in profile.numeric_cols else 0)
        task = detect_task(df[target])
        st.info(f"Detected task: **{task}**")

        if st.button("🚀 Train Models"):
            try:
                with st.spinner("Training models..."):
                    result = train_models(df, target)
                st.session_state["ml_result"] = result
                st.success(f"✅ Best model: {result.best_model}")
            except Exception as e:
                log.error(f"ML training failed: {e}", exc_info=True)
                st.error(f"Training failed: {e}")

        result = st.session_state.get("ml_result")
        if result:
            st.markdown("### Model Comparison")
            comp_df = pd.DataFrame(result.models).T
            st.dataframe(comp_df.round(4), use_container_width=True)

            st.markdown("### Feature Importance")
            if result.feature_importance:
                fi_df = pd.DataFrame(list(result.feature_importance.items()),
                                     columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)
                fig = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                             title="Top Features", color="Importance",
                             color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)

            if result.metrics.get("confusion_matrix"):
                st.markdown("### Confusion Matrix")
                cm = result.metrics["confusion_matrix"]
                fig = go.Figure(data=go.Heatmap(z=cm, colorscale="Blues"))
                fig.update_layout(title="Confusion Matrix", height=350)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### K-Means Clustering")
        k = st.slider("Number of clusters (K)", 2, 10, 4)
        if st.button("🔍 Run Clustering"):
            try:
                with st.spinner("Clustering..."):
                    res = cluster_data(df, k=k)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.session_state["cluster_result"] = res
                    st.success(f"✅ Found {k} clusters, inertia = {res['inertia']:.2f}")
            except Exception as e:
                st.error(f"Clustering failed: {e}")

        cl = st.session_state.get("cluster_result")
        if cl and "labels" in cl:
            num_df = df.select_dtypes(include="number").dropna().copy()
            num_df["Cluster"] = cl["labels"]
            if len(num_df.columns) >= 3:
                fig = px.scatter_matrix(num_df, dimensions=num_df.columns[:4],
                                        color="Cluster", title="Cluster Profile")
                st.plotly_chart(fig, use_container_width=True)