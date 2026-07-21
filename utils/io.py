"""File ingestion with encoding detection & validation."""
from __future__ import annotations
import io
from pathlib import Path
from typing import Tuple
import pandas as pd
import polars as pl
from config.settings import settings
from utils.logger import log

ALLOWED = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv", ".feather", ".zip"}


def detect_encoding(path: Path) -> str:
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read(200_000)
        return chardet.detect(raw).get("encoding") or "utf-8"
    except Exception:
        return "utf-8"


def validate_file(name: str, size_bytes: int) -> None:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED}")
    if size_bytes > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"File exceeds {settings.MAX_UPLOAD_MB}MB limit")


def load_dataset(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    log.info(f"Loading {path.name} ({ext})")
    try:
        if ext == ".csv":
            enc = detect_encoding(path)
            try:
                df = pd.read_csv(path, encoding=enc, low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="latin-1", low_memory=False)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        elif ext == ".json":
            df = pd.read_json(path)
        elif ext == ".parquet":
            df = pd.read_parquet(path)
        elif ext == ".tsv":
            df = pd.read_csv(path, sep="\t", encoding=detect_encoding(path))
        elif ext == ".feather":
            df = pd.read_feather(path)
        elif ext == ".zip":
            df = pd.read_csv(path, compression="zip", encoding="latin-1")
        else:
            raise ValueError(f"Unsupported extension: {ext}")
    except Exception as e:
        log.error(f"Failed to load {path.name}: {e}", exc_info=True)
        raise

    # Normalize column names
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
    log.info(f"Loaded {df.shape[0]:,} rows x {df.shape[1]} cols")
    return df


def sample_for_display(df: pd.DataFrame, n: int = 5_000) -> pd.DataFrame:
    return df.head(n) if len(df) > n else df