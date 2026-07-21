"""Automatic dataset profiling & column type inference."""
from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from typing import Literal
from utils.logger import log


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    inferred_type: Literal["numeric", "categorical", "datetime", "boolean", "text", "id"]
    missing: int
    missing_pct: float
    unique: int
    unique_pct: float
    sample: list
    stats: dict


@dataclass
class Profile:
    rows: int
    cols: int
    memory_mb: float
    duplicate_rows: int
    duplicate_cols: list
    numeric_cols: list
    categorical_cols: list
    datetime_cols: list
    text_cols: list
    id_cols: list
    boolean_cols: list
    target_suggestion: str | None
    columns: list[dict]
    quality_score: float
    issues: list[str]


def _infer_type(s: pd.Series) -> str:
    n = len(s)
    if n == 0:
        return "text"
    unique = s.nunique(dropna=True)
    if pd.api.types.is_bool_dtype(s):
        return "boolean"
    if pd.api.types.is_numeric_dtype(s):
        return "id" if unique == n and unique > 1000 else "numeric"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "datetime"
    # try parse datetime
    sample = s.dropna().astype(str).head(50)
    if len(sample) > 0:
        try:
            parsed = pd.to_datetime(sample, errors="raise", infer_datetime_format=True)
            if (parsed.notna()).mean() > 0.8:
                return "datetime"
        except Exception:
            pass
    if unique == n and n > 50:
        return "id"
    if unique <= max(30, n * 0.05):
        return "categorical"
    return "text"


def profile_dataset(df: pd.DataFrame) -> Profile:
    log.info(f"Profiling dataset {df.shape}")
    n = len(df)
    col_infos: list[ColumnInfo] = []
    dup_cols = df.columns[df.columns.duplicated()].tolist()
    issues: list[str] = []

    for col in df.columns:
        s = df[col]
        inferred = _infer_type(s)
        missing = int(s.isna().sum())
        unique = int(s.nunique(dropna=True))
        stats = {}
        if inferred == "numeric":
            stats = {
                "mean": float(s.mean()) if not s.empty else None,
                "median": float(s.median()) if not s.empty else None,
                "std": float(s.std()) if not s.empty else None,
                "min": float(s.min()) if not s.empty else None,
                "max": float(s.max()) if not s.empty else None,
                "q25": float(s.quantile(.25)) if not s.empty else None,
                "q75": float(s.quantile(.75)) if not s.empty else None,
            }
        elif inferred == "categorical":
            vc = s.value_counts().head(5)
            stats = {"top_values": {str(k): int(v) for k, v in vc.items()}}
        col_infos.append(ColumnInfo(
            name=str(col), dtype=str(s.dtype), inferred_type=inferred,
            missing=missing, missing_pct=round(missing/n*100, 2) if n else 0,
            unique=unique, unique_pct=round(unique/n*100, 2) if n else 0,
            sample=s.dropna().head(3).astype(str).tolist(), stats=stats
        ))
        if missing > 0:
            issues.append(f"{col}: {missing} missing values ({missing/n*100:.1f}%)")

    dup_rows = int(df.duplicated().sum())
    if dup_rows > 0:
        issues.append(f"{dup_rows} duplicate rows detected")
    if dup_cols:
        issues.append(f"Duplicate columns: {dup_cols}")

    # Target suggestion: highest-cardinality numeric, or column named like target
    target = None
    name_hints = ["target", "label", "revenue", "sales", "price", "amount", "churn", "default"]
    numeric_cols = [c.name for c in col_infos if c.inferred_type == "numeric"]
    for hint in name_hints:
        for c in col_infos:
            if hint in c.name.lower() and c.inferred_type in ("numeric", "boolean", "categorical"):
                target = c.name
                break
        if target:
            break
    if not target and numeric_cols:
        target = numeric_cols[-1]

    # Quality score
    total_cells = n * len(df.columns) if n else 0
    miss_cells = sum(c.missing for c in col_infos)
    quality = max(0.0, 1 - (miss_cells / total_cells if total_cells else 0) - (dup_rows / n if n else 0) * 0.1)
    quality = round(quality * 100, 1)

    return Profile(
        rows=n, cols=len(df.columns), memory_mb=round(df.memory_usage(deep=True).sum()/1e6, 2),
        duplicate_rows=dup_rows, duplicate_cols=dup_cols,
        numeric_cols=numeric_cols,
        categorical_cols=[c.name for c in col_infos if c.inferred_type == "categorical"],
        datetime_cols=[c.name for c in col_infos if c.inferred_type == "datetime"],
        text_cols=[c.name for c in col_infos if c.inferred_type == "text"],
        id_cols=[c.name for c in col_infos if c.inferred_type == "id"],
        boolean_cols=[c.name for c in col_infos if c.inferred_type == "boolean"],
        target_suggestion=target,
        columns=[asdict(c) for c in col_infos],
        quality_score=quality,
        issues=issues,
    )