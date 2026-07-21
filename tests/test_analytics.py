"""Unit tests for analytics modules."""
import pandas as pd
import numpy as np
import pytest
from analytics.profiler import profile_dataset
from analytics.kpis import generate_kpis
from analytics.cleaner import fill_missing, drop_duplicates
from analytics.insights import generate_insights


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
        "revenue": np.random.gamma(2, 100, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
        "customer_id": range(100),
    })


def test_profiler(sample_df):
    p = profile_dataset(sample_df)
    assert p.rows == 100
    assert "revenue" in p.numeric_cols
    assert p.quality_score > 0


def test_kpis(sample_df):
    p = profile_dataset(sample_df)
    k = generate_kpis(sample_df, p)
    assert "Total Revenue" in k
    assert k["Total Revenue"] > 0


def test_cleaning(sample_df):
    df = sample_df.copy()
    df.loc[0, "revenue"] = np.nan
    cleaned = fill_missing(df)
    assert cleaned["revenue"].isna().sum() == 0


def test_insights(sample_df):
    p = profile_dataset(sample_df)
    ins = generate_insights(sample_df, p)
    assert len(ins) > 0
    assert all("title" in i and "body" in i for i in ins)