"""Price-only validation tuning and a final untouched chronological holdout."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import forward_open_log_return, validate_ohlcv

HORIZONS = (1, 3, 7, 30)
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)


def make_features(frame: pd.DataFrame) -> pd.DataFrame:
    """All predictors use only BTC close prices available at signal close t."""
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


def _ridge_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray,
                   alpha: float = 10.0) -> np.ndarray:
    mean = x_train.mean(axis=0)
    # NumPy 2.4 may expose a read-only reduction view; own a writable copy.
    scale = np.array(x_train.std(axis=0), dtype=float, copy=True)
    scale[scale < 1e-12] = 1.0
    x = (x_train - mean) / scale
    xt = (x_test - mean) / scale
    y_mean = float(y_train.mean())
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (y_train - y_mean))
    return y_mean + xt @ beta


def _valid_indices(target: pd.Series, features: pd.DataFrame, indices: np.ndarray) -> np.ndarray:
    mask = target.iloc[indices].notna().to_numpy()
    mask &= features.iloc[indices].notna().all(axis=1).to_numpy()
    return indices[mask]


def walk_forward(frame: pd.DataFrame, min_train_rows: int = 1095,
                 holdout_rows: int = 365) -> tuple[pd.DataFrame, dict]:
    """Tune Ridge only on a purged validation slice; evaluate once on untouched final holdout.

    Training labels are required to mature before the validation/holdout boundary.
    No observation from the final holdout is ever used to fit or tune a model.
    """
    validate_ohlcv(frame)
    data = frame.sort_values("timestamp").reset_index(drop=True).copy()
    features = make_features(data)
    n = len(data)
    holdout_start = n - holdout_rows
    if holdout_start <= min_train_rows + 100:
        return pd.DataFrame(), {"status": "BLOCKED", "reason": "insufficient pre-holdout history",
                                "rows": n, "holdout_rows": holdout_rows}
    outputs, tuning = [], {}
    for horizon in HORIZONS:
        target = forward_open_log_return(data["open"], horizon)
        # Keep the validation slice strictly before the final holdout.
        validation_start = int(holdout_start * 0.85)
        validation_train_end = validation_start - horizon - 2
        validation_train_idx = _valid_indices(
            target, features, np.arange(61, max(61, validation_train_end + 1))
        )
        validation_idx = _valid_indices(
            target, features,
            np.arange(validation_start, max(validation_start, holdout_start - horizon - 1)),
        )
        if len(validation_train_idx) < min_train_rows or len(validation_idx) < 30:
            return pd.DataFrame(), {
                "status": "BLOCKED", "reason": f"insufficient purged validation data for h={horizon}",
                "rows": n, "holdout_start": str(data.timestamp.iloc[holdout_start]),
            }
        x_val_train = features.iloc[validation_train_idx].to_numpy(dtype=float)
        y_val_train = target.iloc[validation_train_idx].to_numpy(dtype=float)
        x_val = features.iloc[validation_idx].to_numpy(dtype=float)
        y_val = target.iloc[validation_idx].to_numpy(dtype=float)
        alpha_scores = {}
        for alpha in RIDGE_ALPHAS:
            val_prediction = _ridge_predict(x_val_train, y_val_train, x_val, alpha)
            alpha_scores[str(alpha)] = float(np.mean(np.abs(val_prediction - y_val)))
        selected_alpha = min(RIDGE_ALPHAS, key=lambda a: alpha_scores[str(a)])
        # All final-training labels must have exited by the first holdout signal close.
        final_train_end = holdout_start - horizon - 2
        final_train_idx = _valid_indices(target, features, np.arange(61, final_train_end + 1))
        holdout_idx = _valid_indices(
            target, features, np.arange(holdout_start, max(holdout_start, n - horizon - 1))
        )
        if len(final_train_idx) < min_train_rows or len(holdout_idx) < 200:
            return pd.DataFrame(), {
                "status": "BLOCKED", "reason": f"insufficient final training/holdout sample for h={horizon}",
                "train_rows": len(final_train_idx), "holdout_rows": len(holdout_idx),
                "required_holdout_rows": 200,
            }
        x_train = features.iloc[final_train_idx].to_numpy(dtype=float)
        y_train = target.iloc[final_train_idx].to_numpy(dtype=float)
        x_test = features.iloc[holdout_idx].to_numpy(dtype=float)
        ridge = _ridge_predict(x_train, y_train, x_test, selected_alpha)
        drift = float(y_train.mean())
        momentum_scale = float(np.mean(np.abs(y_train)))
        momentum_sign = np.sign(
            np.log(data["close"].iloc[holdout_idx].to_numpy(dtype=float)
                   / data["close"].shift(20).iloc[holdout_idx].to_numpy(dtype=float))
        )
        momentum = momentum_sign * momentum_scale
        for j, t in enumerate(holdout_idx):
            outputs.append({
                "timestamp": data["timestamp"].iloc[t].isoformat(), "horizon": horizon,
                "split": "final_holdout", "actual": float(target.iloc[t]), "zero": 0.0,
                "drift": drift, "momentum": float(momentum[j]), "ridge": float(ridge[j]),
                "train_rows": len(final_train_idx), "selected_alpha": selected_alpha,
            })
        tuning[str(horizon)] = {
            "selected_alpha": selected_alpha, "validation_mae_by_alpha": alpha_scores,
            "validation_rows": len(validation_idx), "final_train_rows": len(final_train_idx),
            "final_holdout_rows": len(holdout_idx),
        }
    predictions = pd.DataFrame(outputs)
    summary = score_predictions(predictions)
    summary.update({
        "validation_tuning": tuning,
        "holdout_start_utc": data.timestamp.iloc[holdout_start].isoformat(),
        "holdout_end_utc": data.timestamp.iloc[-1].isoformat(),
        "holdout_is_untouched": True,
        "training_uses_holdout": False,
        "features": "price-only BTC close returns, rolling volatility and trend",
        "target": "log(Open[t+h+1]/Open[t+1]); signal after close t; entry next open",
    })
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
                "n": len(y), "mae": float(np.mean(np.abs(err))),
                "rmse": float(np.sqrt(np.mean(err ** 2))),
                "directional_accuracy": float(np.mean(np.sign(p) == np.sign(y))),
                "mean_error": float(np.mean(err)),
            }
        results[str(int(horizon))] = scores
    return {
        "status": "SCORED_NOT_PROMOTED", "holdout_metrics": results,
        "promotion": "No promotion. Require >=200 matured OOS forecasts per horizon, robust lift, calibration, regime stability and cost tests.",
    }


def cross_check_venues(primary: pd.DataFrame, secondary: pd.DataFrame) -> dict:
    """Compare aligned daily returns; never concatenate venues or quote currencies."""
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
        "status": "PASS" if np.isfinite(corr) else "WARN", "overlap_rows": len(aligned),
        "return_correlation": corr,
        "median_absolute_log_basis": float(basis.abs().median()),
        "p99_absolute_log_basis": float(basis.abs().quantile(0.99)),
        "warning": "USDT/USD quote basis is not FX-adjusted; venues remain separate.",
    }
