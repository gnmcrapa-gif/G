"""Pre-registered OHLCV feature challenger; strictly prospective, never promoted here."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from .research import HORIZONS, _ridge_predict, make_features
from .validation import EXECUTION_ENTRY_LAG_SESSIONS, forward_open_log_return

OHLCV_EXPERIMENT_ID = "V5.5-OHLCV-001"
HISTORICAL_HOLDOUT_START_UTC = pd.Timestamp("2025-11-16T00:00:00Z")
FIXED_ALPHA = 100.0


def make_ohlcv_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create point-in-time price, volume-surprise and candle-geometry features."""
    features = make_features(frame)
    open_price = pd.to_numeric(frame["open"], errors="raise").astype(float)
    high = pd.to_numeric(frame["high"], errors="raise").astype(float)
    low = pd.to_numeric(frame["low"], errors="raise").astype(float)
    close = pd.to_numeric(frame["close"], errors="raise").astype(float)
    volume = pd.to_numeric(frame["volume"], errors="raise").astype(float)

    log_volume = np.log1p(volume)
    prior_median = log_volume.rolling(30, min_periods=30).median().shift(1)
    prior_mad = log_volume.rolling(30, min_periods=30).apply(
        lambda values: float(np.median(np.abs(values - np.median(values)))), raw=True
    ).shift(1)
    robust_scale = (1.4826 * prior_mad).where(prior_mad > 1e-12, np.nan)
    features["volume_surprise_log_30"] = log_volume - prior_median
    features["volume_surprise_robust_z_30"] = (log_volume - prior_median) / robust_scale

    candle_range = (high - low).clip(lower=0.0)
    features["range_pct"] = candle_range / open_price
    features["body_pct"] = (close - open_price) / open_price
    features["upper_wick_pct"] = (high - np.maximum(open_price, close)) / open_price
    features["lower_wick_pct"] = (np.minimum(open_price, close) - low) / open_price
    features["close_location"] = (
        (close - low) / candle_range.replace(0.0, np.nan)
    ).fillna(0.5)
    return features.replace([np.inf, -np.inf], np.nan)


def generate_ohlcv_forecast_events(
    frame: pd.DataFrame,
    manifest_sha256: str,
    code_commit: str,
    *,
    min_train_rows: int = 1095,
    now: datetime | None = None,
) -> list[dict]:
    """Emit point forecasts trained only before the frozen historical holdout.

    Alpha is fixed at 100 from the existing price-only validation convention; this
    experiment does not tune on the historical continuity window or on future outcomes.
    """
    data = frame.sort_values("timestamp").reset_index(drop=True).copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    features = make_ohlcv_features(data)
    holdout_start_idx = int(
        data["timestamp"].searchsorted(HISTORICAL_HOLDOUT_START_UTC, side="left")
    )
    if holdout_start_idx <= min_train_rows + 100:
        return []
    current = now or datetime.now(UTC)
    current_ts = pd.Timestamp(current)
    if current_ts.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current_ts = current_ts.tz_convert("UTC")
    t = len(data) - 1
    if t < holdout_start_idx:
        return []

    signal_ts = pd.Timestamp(data.loc[t, "timestamp"])
    feature_cutoff = signal_ts + pd.Timedelta(days=1)
    close = data["close"].astype(float)
    sma200 = close.rolling(200, min_periods=200).mean()
    if pd.isna(sma200.iloc[t]) or pd.isna(sma200.iloc[max(0, t - 20)]):
        regime = "unclassified"
    elif close.iloc[t] > sma200.iloc[t] and sma200.iloc[t] > sma200.iloc[t - 20]:
        regime = "bull"
    elif close.iloc[t] < sma200.iloc[t] and sma200.iloc[t] < sma200.iloc[t - 20]:
        regime = "bear"
    else:
        regime = "range"

    events = []
    for horizon in HORIZONS:
        target = forward_open_log_return(
            data["open"], horizon, entry_lag_sessions=EXECUTION_ENTRY_LAG_SESSIONS
        )
        # Last training label must finish before the first historical holdout candle.
        last_train = holdout_start_idx - horizon - EXECUTION_ENTRY_LAG_SESSIONS - 1
        train_idx = np.arange(61, max(61, last_train + 1))
        valid = (
            target.iloc[train_idx].notna().to_numpy()
            & features.iloc[train_idx].notna().all(axis=1).to_numpy()
        )
        train_idx = train_idx[valid]
        x_now = features.iloc[t].to_numpy(dtype=float)
        if len(train_idx) < min_train_rows or not np.isfinite(x_now).all():
            continue
        x_train = features.iloc[train_idx].to_numpy(dtype=float)
        y_train = target.iloc[train_idx].to_numpy(dtype=float)
        prediction = float(_ridge_predict(
            x_train, y_train, x_now.reshape(1, -1), FIXED_ALPHA
        )[0])
        drift = float(y_train.mean())
        momentum_scale = float(np.mean(np.abs(y_train)))
        momentum_sign = np.sign(np.log(close.iloc[t] / close.iloc[t - 20]))
        benchmarks = {
            "zero_return": 0.0,
            "training_drift": drift,
            "fixed_momentum": float(momentum_sign * momentum_scale),
        }
        model_version = f"ohlcv-challenger-0.1-fixed-alpha-{FIXED_ALPHA:g}"
        forecast_id = hashlib.sha256(
            f"{signal_ts.isoformat()}|{horizon}|{model_version}|{manifest_sha256}".encode()
        ).hexdigest()[:24]
        entry = signal_ts + pd.Timedelta(days=EXECUTION_ENTRY_LAG_SESSIONS)
        expiry = signal_ts + pd.Timedelta(days=horizon + EXECUTION_ENTRY_LAG_SESSIONS)
        if entry <= current_ts:
            continue
        training_cutoff = pd.Timestamp(data.loc[last_train, "timestamp"])
        events.append({
            "event_id": f"forecast-{forecast_id}",
            "event_type": "FORECAST",
            "forecast_id": forecast_id,
            "recorded_at_utc": current_ts.isoformat(),
            "issued_at_utc": current_ts.isoformat(),
            "model_version": model_version,
            "code_commit": code_commit,
            "data_manifest_sha256": manifest_sha256,
            "target": f"log(Open[t+h+{EXECUTION_ENTRY_LAG_SESSIONS}]/Open[t+{EXECUTION_ENTRY_LAG_SESSIONS}])",
            "horizon": horizon,
            "signal_timestamp_utc": signal_ts.isoformat(),
            "feature_cutoff_utc": feature_cutoff.isoformat(),
            "regime_ex_ante": regime,
            "forecast": prediction,
            "benchmark_forecasts": json.dumps(benchmarks, sort_keys=True),
            "entry_timestamp_utc": entry.isoformat(),
            "expiry_timestamp_utc": expiry.isoformat(),
            "scoring_status": "PENDING",
            "notes": (
                f"{OHLCV_EXPERIMENT_ID}; prospective-only; fixed alpha={FIXED_ALPHA:g}; "
                f"training_cutoff_utc={training_cutoff.isoformat()}; "
                f"holdout_start_utc={HISTORICAL_HOLDOUT_START_UTC.isoformat()}; "
                "historical holdout excluded from training and tuning; no probability claim."
            ),
        })
    return events
