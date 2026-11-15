"""Chronological walk-forward forecasts; no tuning on the final holdout."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import forward_open_log_return, validate_ohlcv

HORIZONS = (1, 3, 7, 30)


def make_features(frame: pd.DataFrame) -> pd.DataFrame:
    close = frame["close"].astype(float)
    log_close = np.log(close)
    features = pd.DataFrame(index=frame.index)
    for lag in (1, 2, 3, 7, 14, 30, 60):
        features[f"ret_{lag}"] = log_close.diff(lag)
    daily = log_close.diff()
    for window in (7, 30):
        features[f"vol_{window}"] = daily.rolling(window, min_periods=window).std()
    features["trend_20"] = log_close - log_close.shift(20)
    features["trend_60"] = log_close - log_close.shift(60)
    return features.replace([np.inf, -np.inf], np.nan)


def _ridge_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, alpha: float = 10.0) -> float:
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    x = (x_train - mean) / scale
    xt = (x_test - mean) / scale
    y_mean = float(y_train.mean())
    centered = y_train - y_mean
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ centered)
    return float(y_mean + xt @ beta)


def walk_forward(frame: pd.DataFrame, min_train_rows: int = 730, ridge_alpha: float = 10.0) -> tuple[pd.DataFrame, dict]:
    """Expanding-window OOS forecasts. Training labels must have matured by signal close."""
    validate_ohlcv(frame)
    data = frame.sort_values("timestamp").reset_index(drop=True).copy()
    features = make_features(data)
    outputs = []
    start = max(min_train_rows + 61, 0)
    for horizon in HORIZONS:
        target = forward_open_log_return(data["open"], horizon)
        for t in range(start, len(data) - horizon - 1):
            last_train = t - horizon - 1
            if last_train < 0:
                continue
            train_idx = np.arange(0, last_train + 1)
            valid = target.iloc[train_idx].notna().to_numpy() & features.iloc[train_idx].notna().all(axis=1).to_numpy()
            train_idx = train_idx[valid]
            if len(train_idx) < min_train_rows:
                continue
            y_train = target.iloc[train_idx].to_numpy(dtype=float)
            x_train = features.iloc[train_idx].to_numpy(dtype=float)
            x_now = features.iloc[t].to_numpy(dtype=float)
            if not np.isfinite(x_now).all():
                continue
            drift = float(y_train.mean())
            momentum_scale = float(np.mean(np.abs(y_train)))
            momentum_sign = np.sign(np.log(data["close"].iloc[t] / data["close"].iloc[t - 20]))
            ridge = _ridge_predict(x_train, y_train, x_now.reshape(1, -1), ridge_alpha)
            actual = float(target.iloc[t])
            outputs.append({
                "timestamp": data["timestamp"].iloc[t].isoformat(),
                "horizon": horizon,
                "actual": actual,
                "zero": 0.0,
                "drift": drift,
                "momentum": float(momentum_sign * momentum_scale),
                "ridge": ridge,
                "train_rows": int(len(train_idx)),
            })
    predictions = pd.DataFrame(outputs)
    summary = score_predictions(predictions)
    return predictions, summary


def score_predictions(predictions: pd.DataFrame) -> dict:
    if predictions.empty:
        return {"status": "BLOCKED", "reason": "no out-of-sample forecasts"}
    results = {}
    for horizon, group in predictions.groupby("horizon"):
        y = group["actual"].to_numpy(dtype=float)
        scores = {}
        for model in ("zero", "drift", "momentum", "ridge"):
            p = group[model].to_numpy(dtype=float)
            err = p - y
            scores[model] = {
                "n": int(len(y)),
                "mae": float(np.mean(np.abs(err))),
                "rmse": float(np.sqrt(np.mean(err ** 2))),
                "directional_accuracy": float(np.mean(np.sign(p) == np.sign(y))),
                "mean_error": float(np.mean(err)),
            }
        results[str(int(horizon))] = scores
    return {"status": "SCORED_NOT_PROMOTED", "horizons": results,
            "promotion": "No promotion is automatic; require >=200 matured OOS forecasts per horizon, robust lift, calibration, regime stability and cost tests."}


def cross_check_venues(primary: pd.DataFrame, secondary: pd.DataFrame) -> dict:
    """Compare aligned daily returns and quote-basis diagnostics without merging price series."""
    left = primary[["timestamp", "close"]].copy()
    right = secondary[["timestamp", "close"]].copy()
    left["timestamp"] = pd.to_datetime(left["timestamp"], utc=True).dt.floor("D")
    right["timestamp"] = pd.to_datetime(right["timestamp"], utc=True).dt.floor("D")
    left = left.drop_duplicates("timestamp").set_index("timestamp").sort_index()
    right = right.drop_duplicates("timestamp").set_index("timestamp").sort_index()
    aligned = left.join(right, how="inner", lsuffix="_primary", rsuffix="_secondary")
    if len(aligned) < 30:
        return {"status": "WARN", "overlap_rows": len(aligned),
                "reason": "fewer than 30 overlapping daily closes; no correlation claim"}
    ret_left = np.log(aligned["close_primary"]).diff()
    ret_right = np.log(aligned["close_secondary"]).diff()
    corr = float(ret_left.corr(ret_right))
    basis = np.log(aligned["close_primary"] / aligned["close_secondary"])
    return {
        "status": "PASS" if np.isfinite(corr) else "WARN",
        "overlap_rows": int(len(aligned)),
        "return_correlation": corr,
        "median_absolute_log_basis": float(basis.abs().median()),
        "p99_absolute_log_basis": float(basis.abs().quantile(0.99)),
        "warning": "USDT/USD quote basis is not FX-adjusted; venues remain separate and are not concatenated.",
    }
