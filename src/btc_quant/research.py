"""Price-only research with purged multi-fold tuning and untouched final holdout."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .validation import forward_open_log_return, validate_ohlcv

HORIZONS = (1, 3, 7, 30)
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
MODELS = ("zero", "drift", "momentum", "ridge")


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
    if not np.isfinite(x_train).all() or not np.isfinite(y_train).all() \
            or not np.isfinite(x_test).all():
        raise ValueError("Ridge inputs must be finite")
    if alpha <= 0 or not np.isfinite(alpha):
        raise ValueError("Ridge alpha must be finite and positive")
    mean = x_train.mean(axis=0)
    scale = np.array(x_train.std(axis=0), dtype=float, copy=True)
    scale[scale < 1e-12] = 1.0
    x = (x_train - mean) / scale
    xt = (x_test - mean) / scale
    y_mean = float(y_train.mean())
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (y_train - y_mean))
    return y_mean + xt @ beta


def _valid_indices(target: pd.Series, features: pd.DataFrame, indices: np.ndarray) -> np.ndarray:
    mask = target.iloc[indices].notna().to_numpy(dtype=bool, copy=True)
    feature_mask = features.iloc[indices].notna().all(axis=1).to_numpy(dtype=bool, copy=True)
    return indices[mask & feature_mask]


def _regime_labels(close: pd.Series) -> pd.Series:
    """Ex-ante trend regime; no future values enter the label."""
    sma = close.astype(float).rolling(200, min_periods=200).mean()
    slope = sma - sma.shift(20)
    labels = pd.Series("unclassified", index=close.index, dtype="object")
    labels.loc[(close > sma) & (slope > 0)] = "bull"
    labels.loc[(close < sma) & (slope < 0)] = "bear"
    labels.loc[sma.notna() & ~(((close > sma) & (slope > 0)) |
                               ((close < sma) & (slope < 0)))] = "range"
    return labels


def _hac_loss_difference(challenger: np.ndarray, benchmark: np.ndarray,
                         actual: np.ndarray, max_lag: int) -> dict:
    """Newey-West paired absolute-loss comparison; positive mean means challenger is worse."""
    difference = np.abs(challenger - actual) - np.abs(benchmark - actual)
    n = len(difference)
    mean = float(difference.mean())
    centered = difference - mean
    lag = min(max_lag, n - 1)
    long_run_variance = float(np.dot(centered, centered) / n)
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        autocov = float(np.dot(centered[k:], centered[:-k]) / n)
        long_run_variance += 2.0 * weight * autocov
    standard_error = math.sqrt(max(long_run_variance, 0.0) / n)
    if standard_error == 0.0:
        z_score = 0.0 if mean == 0.0 else None
        p_value = 1.0 if mean == 0.0 else 0.0
    else:
        z_score = mean / standard_error
        p_value = math.erfc(abs(z_score) / math.sqrt(2.0))
    return {
        "n": n, "mean_absolute_loss_difference": mean,
        "hac_standard_error": standard_error, "z_score": z_score,
        "two_sided_p_value_normal_approx": p_value,
        "hac_lags": lag,
        "interpretation": "challenger_worse" if mean > 0 else (
            "challenger_better" if mean < 0 else "equal"
        ),
        "warning": "Asymptotic normal approximation; overlapping targets use horizon-1 HAC lags.",
    }


def _metric_block(group: pd.DataFrame) -> dict:
    y = group["actual"].to_numpy(dtype=float)
    scores = {}
    for model in MODELS:
        prediction = group[model].to_numpy(dtype=float)
        error = prediction - y
        scores[model] = {
            "n": len(y),
            "mae": float(np.mean(np.abs(error))),
            "rmse": float(np.sqrt(np.mean(error ** 2))),
            "directional_accuracy": (
                None if model == "zero" else float(np.mean(np.sign(prediction) == np.sign(y)))
            ),
            "mean_error": float(np.mean(error)),
        }
    return scores


def walk_forward(frame: pd.DataFrame, min_train_rows: int = 1095,
                 holdout_rows: int = 365) -> tuple[pd.DataFrame, dict]:
    """Tune on three purged expanding validation folds; evaluate once on untouched holdout."""
    validate_ohlcv(frame)
    data = frame.sort_values("timestamp").reset_index(drop=True).copy()
    features = make_features(data)
    regimes = _regime_labels(data["close"])
    n = len(data)
    holdout_start = n - holdout_rows
    if holdout_start <= min_train_rows + 100:
        return pd.DataFrame(), {
            "status": "BLOCKED", "reason": "insufficient pre-holdout history",
            "rows": n, "holdout_rows": holdout_rows,
        }

    outputs, tuning = [], {}
    for horizon in HORIZONS:
        target = forward_open_log_return(data["open"], horizon)
        validation_start = int(holdout_start * 0.80)
        validation_end = holdout_start - horizon - 2
        boundaries = np.linspace(validation_start, validation_end, 4, dtype=int)
        fold_scores = {str(alpha): [] for alpha in RIDGE_ALPHAS}
        fold_counts = []
        for fold_number in range(3):
            fold_start, fold_end = int(boundaries[fold_number]), int(boundaries[fold_number + 1])
            train_end = fold_start - horizon - 3
            train_idx = _valid_indices(
                target, features, np.arange(61, max(61, train_end + 1))
            )
            val_idx = _valid_indices(
                target, features, np.arange(fold_start, max(fold_start, fold_end))
            )
            if len(train_idx) < min_train_rows or len(val_idx) < 30:
                return pd.DataFrame(), {
                    "status": "BLOCKED",
                    "reason": f"insufficient purged validation data for h={horizon}, fold={fold_number + 1}",
                    "train_rows": len(train_idx), "validation_rows": len(val_idx),
                }
            x_train = features.iloc[train_idx].to_numpy(dtype=float)
            y_train = target.iloc[train_idx].to_numpy(dtype=float)
            x_val = features.iloc[val_idx].to_numpy(dtype=float)
            y_val = target.iloc[val_idx].to_numpy(dtype=float)
            for alpha in RIDGE_ALPHAS:
                prediction = _ridge_predict(x_train, y_train, x_val, alpha)
                fold_scores[str(alpha)].append(float(np.mean(np.abs(prediction - y_val))))
            fold_counts.append({"fold": fold_number + 1, "train_rows": len(train_idx),
                                "validation_rows": len(val_idx),
                                "validation_start": data.timestamp.iloc[fold_start].isoformat(),
                                "validation_end": data.timestamp.iloc[fold_end - 1].isoformat()})

        alpha_scores = {
            key: float(np.average(values, weights=[row["validation_rows"] for row in fold_counts]))
            for key, values in fold_scores.items()
        }
        selected_alpha = min(RIDGE_ALPHAS, key=lambda alpha: alpha_scores[str(alpha)])
        final_train_end = holdout_start - horizon - 3
        final_train_idx = _valid_indices(
            target, features, np.arange(61, final_train_end + 1)
        )
        holdout_idx = _valid_indices(
            target, features, np.arange(holdout_start, max(holdout_start, n - horizon - 2))
        )
        if len(final_train_idx) < min_train_rows or len(holdout_idx) < 200:
            return pd.DataFrame(), {
                "status": "BLOCKED",
                "reason": f"insufficient final training/holdout sample for h={horizon}",
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
                "timestamp": data.timestamp.iloc[t].isoformat(), "horizon": horizon,
                "split": "final_holdout", "regime": regimes.iloc[t],
                "actual": float(target.iloc[t]), "zero": 0.0, "drift": drift,
                "momentum": float(momentum[j]), "ridge": float(ridge[j]),
                "train_rows": len(final_train_idx), "selected_alpha": selected_alpha,
            })
        tuning[str(horizon)] = {
            "selected_alpha": selected_alpha, "validation_mae_by_alpha": alpha_scores,
            "validation_folds": fold_counts, "final_train_rows": len(final_train_idx),
            "final_holdout_rows": len(holdout_idx),
        }

    predictions = pd.DataFrame(outputs)
    summary = score_predictions(predictions)
    summary.update({
        "validation_tuning": tuning,
        "validation_method": "three purged expanding chronological folds; alpha chosen by weighted mean MAE",
        "holdout_start_utc": data.timestamp.iloc[holdout_start].isoformat(),
        "holdout_end_utc": data.timestamp.iloc[-1].isoformat(),
        "holdout_is_untouched": True, "training_uses_holdout": False,
        "features": "price-only BTC close returns, rolling volatility and trend",
        "regime_definition": "bull/bear/range from close versus SMA200 and SMA200 20-session slope; ex ante",
        "target": "log(Open[t+h+2]/Open[t+2]); signal after close t; one daily bar latency; entry future open",
    })
    return predictions, summary


def score_predictions(predictions: pd.DataFrame) -> dict:
    if predictions.empty:
        return {"status": "BLOCKED", "reason": "no out-of-sample forecasts"}
    results, paired_tests, regime_results = {}, {}, {}
    for horizon, group in predictions.groupby("horizon"):
        results[str(int(horizon))] = _metric_block(group)
        actual = group["actual"].to_numpy(dtype=float)
        paired_tests[str(int(horizon))] = {
            f"{challenger}_vs_{benchmark}": _hac_loss_difference(
                group[challenger].to_numpy(dtype=float),
                group[benchmark].to_numpy(dtype=float), actual, max_lag=int(horizon) - 1,
            )
            for challenger, benchmark in (("ridge", "zero"), ("ridge", "drift"))
        }
        if "regime" in group.columns:
            regime_results[str(int(horizon))] = {
                str(regime): {"n": len(regime_group), "metrics": _metric_block(regime_group)}
                for regime, regime_group in group.groupby("regime")
            }
    return {
        "status": "SCORED_NOT_PROMOTED", "holdout_metrics": results,
        "paired_loss_tests": paired_tests, "regime_metrics": regime_results,
        "promotion": (
            "No promotion. Require consistent OOS lift over zero and drift, HAC-aware "
            "paired-loss evidence, regime stability, calibration and cost-adjusted tests."
        ),
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
