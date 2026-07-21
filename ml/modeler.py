"""Machine learning pipeline: regression, classification, clustering."""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Literal, Any
from dataclasses import dataclass, asdict
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, mean_squared_error, r2_score,
                             roc_auc_score)
from sklearn.linear_model import LogisticRegression, LinearRegression
from utils.logger import log


@dataclass
class MLResult:
    task: str
    target: str
    models: dict
    best_model: str
    metrics: dict
    feature_importance: dict
    predictions_sample: list


def _prepare_features(df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns=[target])
    y = df[target]
    # Encode categoricals
    for col in X.select_dtypes(include="object").columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    X = X.fillna(X.median(numeric_only=True))
    return X, y


def detect_task(y: pd.Series) -> Literal["classification", "regression"]:
    if y.dtype == object or y.nunique() <= 20:
        return "classification"
    return "regression"


def train_models(df: pd.DataFrame, target: str) -> MLResult:
    task = detect_task(df[target])
    X, y = _prepare_features(df, target)

    if task == "classification":
        # encode target if needed
        if y.dtype == object:
            y = LabelEncoder().fit_transform(y)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        }
        metrics_fn = lambda yt, yp: {
            "accuracy": float(accuracy_score(yt, yp)),
            "precision": float(precision_score(yt, yp, average="weighted", zero_division=0)),
            "recall": float(recall_score(yt, yp, average="weighted", zero_division=0)),
            "f1": float(f1_score(yt, yp, average="weighted", zero_division=0)),
        }
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        models = {
            "Linear Regression": LinearRegression(),
            "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        }
        metrics_fn = lambda yt, yp: {
            "r2": float(r2_score(yt, yp)),
            "rmse": float(np.sqrt(mean_squared_error(yt, yp))),
        }

    results: dict[str, dict] = {}
    best_name, best_score = None, -np.inf
    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            m = metrics_fn(y_test, preds)
            cv = cross_val_score(model, X, y, cv=3, scoring="accuracy" if task == "classification" else "r2")
            m["cv_mean"] = float(cv.mean())
            m["cv_std"] = float(cv.std())
            results[name] = m
            score = m.get("accuracy", m.get("r2", 0))
            if score > best_score:
                best_score, best_name = score, name
        except Exception as e:
            log.warning(f"Model {name} failed: {e}")

    # Feature importance
    fi = {}
    try:
        rf = models.get("Random Forest")
        if rf and hasattr(rf, "feature_importances_"):
            fi = dict(sorted(zip(X.columns, rf.feature_importances_), key=lambda x: -x[1])[:10])
            fi = {str(k): float(v) for k, v in fi.items()}
    except Exception:
        pass

    # Confusion matrix if classification
    cm = None
    if task == "classification":
        try:
            rf = models["Random Forest"]
            preds = rf.predict(X_test)
            cm = confusion_matrix(y_test, preds).tolist()
        except Exception:
            pass

    return MLResult(
        task=task, target=target, models=results, best_model=best_name or "",
        metrics={"confusion_matrix": cm} if cm else {},
        feature_importance=fi,
        predictions_sample=[float(x) for x in models[best_name].predict(X_test)[:10]] if best_name else []
    )


def cluster_data(df: pd.DataFrame, k: int = 4) -> dict[str, Any]:
    num = df.select_dtypes(include=np.number).dropna()
    if len(num.columns) < 2 or len(num) < k:
        return {"error": "Insufficient numeric data for clustering"}
    scaler = StandardScaler()
    scaled = scaler.fit_transform(num)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(scaled)
    return {
        "labels": labels.tolist(),
        "centers": km.cluster_centers_.tolist(),
        "inertia": float(km.inertia_),
        "columns": num.columns.tolist(),
    }