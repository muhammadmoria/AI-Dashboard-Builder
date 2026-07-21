"""Automatic visualization engine."""
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Any
from analytics.profiler import Profile
from config.settings import settings


def _theme_kwargs() -> dict:
    dark = st_session_theme() == "dark"
    return dict(
        template="plotly_dark" if dark else "plotly_white",
        color_discrete_sequence=settings.CHART_PALETTE,
    )


def st_session_theme() -> str:
    import streamlit as st
    return st.session_state.get("theme", "dark")


def auto_generate_charts(df: pd.DataFrame, profile: Profile, max_charts: int = 12) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    kw = _theme_kwargs()

    # 1. Histograms for numeric
    for col in profile.numeric_cols[:4]:
        try:
            fig = px.histogram(df, x=col, nbins=40, title=f"Distribution of {col}", **kw)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            charts.append({"title": f"Distribution: {col}", "type": "histogram", "fig": fig})
        except Exception:
            pass

    # 2. Bar charts for categorical
    for col in profile.categorical_cols[:4]:
        try:
            vc = df[col].value_counts().head(15).reset_index()
            vc.columns = [col, "count"]
            fig = px.bar(vc, x=col, y="count", title=f"Top categories: {col}", **kw)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            charts.append({"title": f"Bar: {col}", "type": "bar", "fig": fig})
        except Exception:
            pass

    # 3. Time series
    if profile.datetime_cols and profile.numeric_cols:
        date_col = profile.datetime_cols[0]
        for num_col in profile.numeric_cols[:2]:
            try:
                ts = df.groupby(df[date_col].dt.to_period("M"))[num_col].sum().reset_index()
                ts[date_col] = ts[date_col].astype(str)
                fig = px.line(ts, x=date_col, y=num_col, title=f"{num_col} over time", **kw)
                fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
                charts.append({"title": f"Trend: {num_col}", "type": "line", "fig": fig})
            except Exception:
                pass

    # 4. Scatter (two numerics)
    if len(profile.numeric_cols) >= 2:
        try:
            fig = px.scatter(df.sample(min(2000, len(df))), x=profile.numeric_cols[0],
                             y=profile.numeric_cols[1],
                             title=f"{profile.numeric_cols[0]} vs {profile.numeric_cols[1]}",
                             opacity=0.6, **kw)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            charts.append({"title": "Scatter", "type": "scatter", "fig": fig})
        except Exception:
            pass

    # 5. Correlation heatmap
    if len(profile.numeric_cols) >= 3:
        try:
            corr = df[profile.numeric_cols].corr().round(2)
            # FIX: Removed zmid=0 and replaced with a proper diverging colorscale
            fig = go.Figure(data=go.Heatmap(
                z=corr.values, x=corr.columns, y=corr.columns,
                colorscale="RdBu", zmid=0))
            fig.update_layout(title="Correlation Matrix", margin=dict(l=10, r=10, t=40, b=10), height=380)
            charts.append({"title": "Correlation Heatmap", "type": "heatmap", "fig": fig})
        except Exception:
            pass

    # 6. Box plot
    if profile.numeric_cols and profile.categorical_cols:
        try:
            cat = profile.categorical_cols[0]
            num = profile.numeric_cols[0]
            top_cats = df[cat].value_counts().head(8).index
            sub = df[df[cat].isin(top_cats)]
            fig = px.box(sub, x=cat, y=num, title=f"{num} by {cat}", **kw)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            charts.append({"title": f"Box: {num} by {cat}", "type": "box", "fig": fig})
        except Exception:
            pass

    # 7. Treemap
    if len(profile.categorical_cols) >= 2:
        try:
            c1, c2 = profile.categorical_cols[0], profile.categorical_cols[1]
            agg = df.groupby([c1, c2]).size().reset_index(name="count").head(100)
            fig = px.treemap(agg, path=[c1, c2], values="count", title=f"Treemap: {c1} → {c2}", **kw)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
            charts.append({"title": "Treemap", "type": "treemap", "fig": fig})
        except Exception:
            pass

    return charts[:max_charts]


def render_chart_grid(charts: list[dict], cols: int = 2) -> None:
    import streamlit as st
    if not charts:
        st.info("No charts available — upload data first.")
        return
    for i in range(0, len(charts), cols):
        row = charts[i:i+cols]
        cs = st.columns(cols)
        for j, ch in enumerate(row):
            with cs[j]:
                st.markdown(f"<div class='glass'>", unsafe_allow_html=True)
                st.plotly_chart(ch["fig"], use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)