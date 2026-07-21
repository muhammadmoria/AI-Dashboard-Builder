"""One-click data cleaning operations with history tracking."""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Callable
import streamlit as st
from utils.logger import log


def _record(op: str, **kwargs) -> None:
    st.session_state["cleaning_history"].append({"op": op, **kwargs})


def fill_missing(df: pd.DataFrame, strategy: str = "auto") -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].isna().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                fill = df[col].median() if strategy in ("auto", "median") else df[col].mean()
                df[col] = df[col].fillna(fill)
            else:
                df[col] = df[col].fillna(df[col].mode().iloc[0]) if not df[col].mode().empty else df[col].fillna("Unknown")
    _record("fill_missing", strategy=strategy)
    log.info(f"Filled missing values using {strategy}")
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    _record("drop_duplicates", removed=before - len(df))
    return df


def drop_empty_cols(df: pd.DataFrame, threshold: float = 0.9) -> pd.DataFrame:
    drop = [c for c in df.columns if df[c].isna().mean() >= threshold]
    df = df.drop(columns=drop)
    _record("drop_empty_cols", cols=drop)
    return df


def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(100)
            try:
                parsed = pd.to_datetime(sample, errors="raise")
                if parsed.notna().mean() > 0.8:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    continue
            except Exception:
                pass
            # Try numeric
            num = pd.to_numeric(df[col], errors="coerce")
            if num.notna().mean() > 0.8:
                df[col] = num
        # Downcast numerics
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast="integer", errors="ignore") \
                if (df[col] % 1 == 0).all() else pd.to_numeric(df[col], downcast="float", errors="ignore")
    _record("convert_dtypes")
    return df


def handle_outliers(df: pd.DataFrame, method: str = "clip") -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=np.number).columns:
        q1, q3 = df[col].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
        if method == "clip":
            df[col] = df[col].clip(lo, hi)
        elif method == "remove":
            df = df[(df[col] >= lo) & (df[col] <= hi)]
    _record("handle_outliers", method=method)
    return df


def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
    _record("normalize_text")
    return df


def undo_last(df: pd.DataFrame) -> pd.DataFrame:
    hist = st.session_state.get("cleaning_history", [])
    if len(hist) <= 1:
        st.session_state["cleaning_history"] = []
        return st.session_state.get("df_original", df)
    st.session_state["cleaning_history"] = hist[:-1]
    return st.session_state.get("df_original", df).copy()


OPERATIONS: dict[str, Callable] = {
    "Fill Missing Values": fill_missing,
    "Drop Duplicates": drop_duplicates,
    "Drop Empty Columns": drop_empty_cols,
    "Auto Type Conversion": convert_dtypes,
    "Handle Outliers": handle_outliers,
    "Normalize Text": normalize_text,
}