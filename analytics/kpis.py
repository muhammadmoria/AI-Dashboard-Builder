"""Automatic KPI generation."""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Any
from analytics.profiler import Profile


REVENUE_HINTS = ["revenue", "sales", "amount", "total", "price", "cost", "profit", "income"]
COUNT_HINTS = ["order", "customer", "product", "id", "transaction"]


def _find(df: pd.DataFrame, hints: list[str], profile: Profile, types: list[str]) -> str | None:
    cols_by_type = {
        "numeric": profile.numeric_cols,
        "categorical": profile.categorical_cols,
        "datetime": profile.datetime_cols,
    }
    candidates = []
    for t in types:
        candidates.extend(cols_by_type.get(t, []))
    for hint in hints:
        for c in candidates:
            if hint in c.lower():
                return c
    return None


def generate_kpis(df: pd.DataFrame, profile: Profile) -> dict[str, Any]:
    kpis: dict[str, Any] = {}
    revenue_col = _find(df, REVENUE_HINTS, profile, ["numeric"])
    id_col = _find(df, COUNT_HINTS, profile, ["id", "categorical"])
    date_col = profile.datetime_cols[0] if profile.datetime_cols else None

    if revenue_col:
        kpis["Total Revenue"] = float(df[revenue_col].sum())
        kpis["Avg Revenue"] = float(df[revenue_col].mean())
        kpis["Median Revenue"] = float(df[revenue_col].median())
        kpis["Revenue Std"] = float(df[revenue_col].std())
    if id_col:
        kpis["Unique Records"] = int(df[id_col].nunique())
    kpis["Total Rows"] = int(len(df))
    if date_col and revenue_col:
        try:
            ts = df.groupby(df[date_col].dt.to_period("M"))[revenue_col].sum()
            if len(ts) >= 2:
                growth = (ts.iloc[-1] - ts.iloc[-2]) / ts.iloc[-2] * 100 if ts.iloc[-2] else 0
                kpis["MoM Growth %"] = float(growth)
        except Exception:
            pass

    # Statistical KPIs for every numeric column
    stats_kpis = {}
    for col in profile.numeric_cols[:6]:
        s = df[col].dropna()
        if len(s):
            stats_kpis[f"{col} (mean)"] = float(s.mean())
            stats_kpis[f"{col} (median)"] = float(s.median())
            stats_kpis[f"{col} (std)"] = float(s.std())
    kpis.update(stats_kpis)

    # Top categories
    for col in profile.categorical_cols[:3]:
        vc = df[col].value_counts().head(3)
        kpis[f"Top {col}"] = {str(k): int(v) for k, v in vc.items()}

    return kpis


def format_kpi(value: Any) -> str:
    if isinstance(value, float):
        if abs(value) >= 1e9: return f"{value/1e9:.2f}B"
        if abs(value) >= 1e6: return f"{value/1e6:.2f}M"
        if abs(value) >= 1e3: return f"{value/1e3:.2f}K"
        if abs(value) < 1: return f"{value:.4f}"
        return f"{value:,.2f}"
    if isinstance(value, dict):
        return " • ".join(f"{k}:{v}" for k, v in list(value.items())[:3])
    return str(value)