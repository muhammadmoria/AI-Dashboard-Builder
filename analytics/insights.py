"""Heuristic AI insights engine with optional LLM augmentation."""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Any
from analytics.profiler import Profile
from analytics.kpis import generate_kpis
from utils.logger import log
from config.settings import settings


def _confidence(base: float, factor: float = 1.0) -> float:
    return round(min(0.99, max(0.3, base * factor)), 2)


def generate_insights(df: pd.DataFrame, profile: Profile) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    kpis = generate_kpis(df, profile)

    # Data quality
    insights.append({
        "category": "Data Quality",
        "title": "Dataset Health Assessment",
        "body": f"Your dataset contains {profile.rows:,} rows and {profile.cols} columns "
                f"with an overall quality score of {profile.quality_score:.1f}/100. "
                f"{'Data is in excellent shape.' if profile.quality_score > 85 else 'Consider cleaning steps to improve reliability.'}",
        "confidence": _confidence(profile.quality_score / 100),
        "severity": "info"
    })

    # Missing values
    if profile.issues:
        insights.append({
            "category": "Data Issues",
            "title": f"{len(profile.issues)} Issues Detected",
            "body": "; ".join(profile.issues[:5]),
            "confidence": 0.95,
            "severity": "warning"
        })

    # Numeric distribution
    for col in profile.numeric_cols[:5]:
        s = df[col].dropna()
        if len(s) < 10: continue
        skew = float(s.skew())
        if abs(skew) > 1:
            insights.append({
                "category": "Distribution",
                "title": f"{col} shows {'right' if skew > 0 else 'left'} skew ({skew:.2f})",
                "body": f"Consider log transformation for {col} to normalize the distribution before modeling.",
                "confidence": _confidence(0.7, 1 - min(abs(skew)/3, 1)),
                "severity": "info"
            })

    # Correlations
    if len(profile.numeric_cols) >= 2:
        corr = df[profile.numeric_cols].corr().abs()
        np.fill_diagonal(corr.values, 0)
        if not corr.empty:
            max_idx = corr.unstack().idxmax()
            if max_idx[0] != max_idx[1]:
                val = corr.loc[max_idx[0], max_idx[1]]
                if val > 0.5:
                    insights.append({
                        "category": "Correlation",
                        "title": f"Strong correlation between {max_idx[0]} and {max_idx[1]}",
                        "body": f"Pearson correlation = {val:.3f}. These variables move together — potential multicollinearity in regression models.",
                        "confidence": _confidence(val),
                        "severity": "info"
                    })

    # Time series trend
    if profile.datetime_cols and profile.numeric_cols:
        date_col = profile.datetime_cols[0]
        num_col = profile.numeric_cols[0]
        try:
            ts = df.groupby(df[date_col].dt.to_period("M"))[num_col].sum().sort_index()
            if len(ts) >= 4:
                slope = np.polyfit(range(len(ts)), ts.values, 1)[0]
                direction = "increasing" if slope > 0 else "decreasing"
                insights.append({
                    "category": "Trend",
                    "title": f"{num_col} is {direction} over time",
                    "body": f"Monthly trend shows {direction} pattern with slope {slope:.2f}.",
                    "confidence": _confidence(0.75),
                    "severity": "info"
                })
        except Exception as e:
            log.debug(f"Trend analysis skipped: {e}")

    # Target suggestion
    if profile.target_suggestion:
        insights.append({
            "category": "Modeling",
            "title": f"Suggested target variable: {profile.target_suggestion}",
            "body": "This column is a strong candidate for supervised learning.",
            "confidence": 0.7,
            "severity": "info"
        })

    # Categorical dominance
    for col in profile.categorical_cols[:3]:
        vc = df[col].value_counts(normalize=True)
        if len(vc) and vc.iloc[0] > 0.7:
            insights.append({
                "category": "Cardinality",
                "title": f"{col} is highly imbalanced",
                "body": f"'{vc.index[0]}' represents {vc.iloc[0]*100:.1f}% of records. Consider stratified sampling.",
                "confidence": _confidence(vc.iloc[0]),
                "severity": "warning"
            })

    # Anomalies (z-score)
    for col in profile.numeric_cols[:3]:
        s = df[col].dropna()
        if len(s) > 30:
            z = (s - s.mean()) / s.std()
            n_out = int((z.abs() > 3).sum())
            if n_out > 0:
                insights.append({
                    "category": "Anomaly",
                    "title": f"{n_out} outliers detected in {col}",
                    "body": f"Records beyond 3σ from the mean. Investigate for data entry errors or rare events.",
                    "confidence": 0.85,
                    "severity": "warning"
                })

    # LLM augmentation (optional)
    if settings.ENABLE_OPENAI:
        try:
            insights.append(_llm_summary(df, profile))
        except Exception as e:
            log.warning(f"LLM insight skipped: {e}")

    return insights


def _llm_summary(df: pd.DataFrame, profile: Profile) -> dict:
    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    sample = df.head(5).to_dict(orient="records")
    prompt = f"Summarize this dataset in 2 sentences for a business executive. Columns: {df.columns.tolist()}. Sample: {sample}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    return {
        "category": "AI Executive Summary",
        "title": "LLM-Generated Summary",
        "body": resp.choices[0].message.content,
        "confidence": 0.9,
        "severity": "info"
    }