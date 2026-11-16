"""Append-only event-sourced forecast ledger."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .research import HORIZONS, _ridge_predict, make_features

LEDGER_COLUMNS = [
    "event_id", "event_type", "forecast_id", "recorded_at_utc", "issued_at_utc",
    "model_version", "code_commit", "data_manifest_sha256", "target", "horizon",
    "signal_timestamp_utc", "feature_cutoff_utc", "regime_ex_ante", "forecast",
    "benchmark_forecasts", "entry_timestamp_utc", "expiry_timestamp_utc",
    "realized_outcome", "forecast_error", "absolute_error", "scoring_status", "notes",
]


def _iso(value: pd.Timestamp) -> str:
    return value.to_pydatetime().isoformat()


def generate_forecast_events(
    frame: pd.DataFrame,
    manifest_sha256: str,
    code_commit: str,
    min_train_rows: int = 1095,
    ridge_alpha: float = 10.0,
) -> list[dict]:
    """Emit point forecasts after the latest complete daily close; no probability claims."""
    data = frame.sort_values("timestamp").reset_index(drop=True)
    features = make_features(data)
    t = len(data) - 1
    if t < 1:
        return []
    signal_ts = pd.Timestamp(data.loc[t, "timestamp"])
    if signal_ts.tzinfo is None:
        signal_ts = signal_ts.tz_localize("UTC")
    else:
        signal_ts = signal_ts.tz_convert("UTC")
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
        target = np.log(data["open"].shift(-(horizon + 1)) / data["open"].shift(-1))
        last_train = t - horizon - 1
        if last_train < 0:
            continue
        train_idx = np.arange(0, last_train + 1)
        valid = target.iloc[train_idx].notna().to_numpy() & features.iloc[train_idx].notna().all(axis=1).to_numpy()
        train_idx = train_idx[valid]
        x_now = features.iloc[t].to_numpy(dtype=float)
        if len(train_idx) < min_train_rows or not np.isfinite(x_now).all():
            continue
        y_train = target.iloc[train_idx].to_numpy(dtype=float)
        x_train = features.iloc[train_idx].to_numpy(dtype=float)
        ridge = _ridge_predict(x_train, y_train, x_now.reshape(1, -1), ridge_alpha)
        drift = float(y_train.mean())
        momentum_scale = float(np.mean(np.abs(y_train)))
        momentum_sign = np.sign(np.log(close.iloc[t] / close.iloc[t - 20]))
        benchmarks = {
            "zero_return": 0.0,
            "training_drift": drift,
            "fixed_momentum": float(momentum_sign * momentum_scale),
        }
        model_version = "ridge-challenger-0.1"
        forecast_id = hashlib.sha256(
            f"{signal_ts.isoformat()}|{horizon}|{model_version}|{manifest_sha256}".encode()
        ).hexdigest()[:24]
        expiry = signal_ts + pd.Timedelta(days=horizon + 1)
        entry = signal_ts + pd.Timedelta(days=1)
        events.append({
            "event_id": f"forecast-{forecast_id}",
            "event_type": "FORECAST",
            "forecast_id": forecast_id,
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "issued_at_utc": datetime.now(UTC).isoformat(),
            "model_version": model_version,
            "code_commit": code_commit,
            "data_manifest_sha256": manifest_sha256,
            "target": "log(Open[t+h+1]/Open[t+1])",
            "horizon": horizon,
            "signal_timestamp_utc": signal_ts.isoformat(),
            "feature_cutoff_utc": feature_cutoff.isoformat(),
            "regime_ex_ante": regime,
            "forecast": ridge,
            "benchmark_forecasts": json.dumps(benchmarks, sort_keys=True),
            "entry_timestamp_utc": entry.isoformat(),
            "expiry_timestamp_utc": expiry.isoformat(),
            "scoring_status": "PENDING",
            "notes": "Point forecast only; challenger, not promoted; no probability claim.",
        })
    return events


def score_matured_events(existing_events: list[dict], frame: pd.DataFrame) -> list[dict]:
    """Append score events for forecasts whose exit open is now available."""
    scored = {row.get("forecast_id") for row in existing_events if row.get("event_type") == "SCORE"}
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    open_by_ts = {row.timestamp: float(row.open) for row in data.itertuples()}
    latest = data["timestamp"].max()
    output = []
    for forecast in existing_events:
        if forecast.get("event_type") != "FORECAST" or forecast.get("forecast_id") in scored:
            continue
        expiry = pd.Timestamp(forecast["expiry_timestamp_utc"])
        entry = pd.Timestamp(forecast["entry_timestamp_utc"])
        if expiry > latest or entry not in open_by_ts or expiry not in open_by_ts:
            continue
        actual = float(np.log(open_by_ts[expiry] / open_by_ts[entry]))
        predicted = float(forecast["forecast"])
        output.append({
            "event_id": f"score-{forecast['forecast_id']}",
            "event_type": "SCORE",
            "forecast_id": forecast["forecast_id"],
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "issued_at_utc": forecast["issued_at_utc"],
            "model_version": forecast["model_version"],
            "code_commit": forecast["code_commit"],
            "data_manifest_sha256": forecast["data_manifest_sha256"],
            "target": forecast["target"],
            "horizon": forecast["horizon"],
            "signal_timestamp_utc": forecast["signal_timestamp_utc"],
            "feature_cutoff_utc": forecast["feature_cutoff_utc"],
            "regime_ex_ante": forecast["regime_ex_ante"],
            "forecast": forecast["forecast"],
            "benchmark_forecasts": forecast["benchmark_forecasts"],
            "entry_timestamp_utc": forecast["entry_timestamp_utc"],
            "expiry_timestamp_utc": forecast["expiry_timestamp_utc"],
            "realized_outcome": actual,
            "forecast_error": predicted - actual,
            "absolute_error": abs(predicted - actual),
            "scoring_status": "SCORED",
            "notes": "Outcome observed from venue-specific Binance BTCUSDT daily open series.",
        })
    return output


def read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != LEDGER_COLUMNS:
            raise ValueError("Forecast ledger schema mismatch; refusing to overwrite or migrate append-only history.")
        return list(reader)


def append_events(path: Path, events: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_events(path)
    known = {row["event_id"] for row in existing}
    new_rows = [row for row in events if row["event_id"] not in known]
    if not new_rows:
        return 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS)
        if path.stat().st_size == 0:
            writer.writeheader()
        for row in new_rows:
            writer.writerow({key: row.get(key, "") for key in LEDGER_COLUMNS})
    return len(new_rows)
