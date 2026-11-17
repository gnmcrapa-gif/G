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
from .validation import EXECUTION_ENTRY_LAG_SESSIONS, forward_open_log_return

def _scalar_float(value, field_name: str) -> float:
    """Parse a scalar or legacy one-element NumPy-array CSV representation."""
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
    array = np.asarray(parsed, dtype=float).reshape(-1)
    if array.size != 1 or not np.isfinite(array[0]):
        raise ValueError(f"{field_name} must contain exactly one finite number")
    return float(array[0])


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
    ridge_alpha_by_horizon: dict[int, float] | None = None,
) -> list[dict]:
    """Emit point forecasts after the latest complete daily close; no probability claims."""
    data = frame.sort_values("timestamp").reset_index(drop=True)
    features = make_features(data)
    now_utc = datetime.now(UTC)
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
        selected_alpha = (ridge_alpha_by_horizon or {}).get(horizon, ridge_alpha)
        target = forward_open_log_return(data["open"], horizon, entry_lag_sessions=EXECUTION_ENTRY_LAG_SESSIONS)
        last_train = t - horizon - EXECUTION_ENTRY_LAG_SESSIONS
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
        ridge = float(_ridge_predict(x_train, y_train, x_now.reshape(1, -1), selected_alpha)[0])
        drift = float(y_train.mean())
        momentum_scale = float(np.mean(np.abs(y_train)))
        momentum_sign = np.sign(np.log(close.iloc[t] / close.iloc[t - 20]))
        benchmarks = {
            "zero_return": 0.0,
            "training_drift": drift,
            "fixed_momentum": float(momentum_sign * momentum_scale),
        }
        model_version = f"ridge-challenger-0.4-multifold-alpha-{selected_alpha:g}"
        forecast_id = hashlib.sha256(
            f"{signal_ts.isoformat()}|{horizon}|{model_version}|{manifest_sha256}".encode()
        ).hexdigest()[:24]
        expiry = signal_ts + pd.Timedelta(days=horizon + EXECUTION_ENTRY_LAG_SESSIONS)
        entry = signal_ts + pd.Timedelta(days=EXECUTION_ENTRY_LAG_SESSIONS)
        # A delayed daily run must never issue a forecast whose entry is already past.
        if entry <= pd.Timestamp(now_utc):
            continue
        events.append({
            "event_id": f"forecast-{forecast_id}",
            "event_type": "FORECAST",
            "forecast_id": forecast_id,
            "recorded_at_utc": now_utc.isoformat(),
            "issued_at_utc": now_utc.isoformat(),
            "model_version": model_version,
            "code_commit": code_commit,
            "data_manifest_sha256": manifest_sha256,
            "target": f"log(Open[t+h+{EXECUTION_ENTRY_LAG_SESSIONS}]/Open[t+{EXECUTION_ENTRY_LAG_SESSIONS}])",
            "horizon": horizon,
            "signal_timestamp_utc": signal_ts.isoformat(),
            "feature_cutoff_utc": feature_cutoff.isoformat(),
            "regime_ex_ante": regime,
            "forecast": ridge,
            "benchmark_forecasts": json.dumps(benchmarks, sort_keys=True),
            "entry_timestamp_utc": entry.isoformat(),
            "expiry_timestamp_utc": expiry.isoformat(),
            "scoring_status": "PENDING",
            "notes": (
                f"Point forecast only; challenger, not promoted; validation-selected "
                f"Ridge alpha={selected_alpha:g}; no probability claim."
            ),
        })
    return events


def invalidate_late_forecasts(existing_events: list[dict]) -> list[dict]:
    """Append invalidations for forecasts issued after their stated entry time."""
    now = pd.Timestamp.now(tz="UTC")
    scored = {row.get("forecast_id") for row in existing_events if row.get("event_type") == "SCORE"}
    invalidated = {row.get("forecast_id") for row in existing_events if row.get("event_type") == "INVALIDATION"}
    output = []
    for forecast in existing_events:
        if forecast.get("event_type") != "FORECAST":
            continue
        forecast_id = forecast.get("forecast_id")
        if forecast_id in scored or forecast_id in invalidated:
            continue
        entry = pd.Timestamp(forecast["entry_timestamp_utc"])
        issued = pd.Timestamp(forecast["issued_at_utc"])
        if entry > issued:
            continue
        output.append({
            "event_id": f"invalidate-{forecast_id}-late-entry",
            "event_type": "INVALIDATION",
            "forecast_id": forecast_id,
            "recorded_at_utc": now.isoformat(),
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
            "scoring_status": "INVALIDATED",
            "notes": "Invalidated: entry timestamp was not in the future at actual issuance; excluded from forecast scoring.",
        })
    return output


def score_matured_events(existing_events: list[dict], frame: pd.DataFrame) -> list[dict]:
    """Append score events for valid forecasts whose exit open is now available."""
    scored = {row.get("forecast_id") for row in existing_events if row.get("event_type") == "SCORE"}
    invalidated = {row.get("forecast_id") for row in existing_events if row.get("event_type") == "INVALIDATION"}
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    open_by_ts = {row.timestamp: float(row.open) for row in data.itertuples()}
    latest = data["timestamp"].max()
    output = []
    for forecast in existing_events:
        if (forecast.get("event_type") != "FORECAST"
                or forecast.get("forecast_id") in scored
                or forecast.get("forecast_id") in invalidated):
            continue
        expiry = pd.Timestamp(forecast["expiry_timestamp_utc"])
        entry = pd.Timestamp(forecast["entry_timestamp_utc"])
        if expiry > latest or entry not in open_by_ts or expiry not in open_by_ts:
            continue
        actual = float(np.log(open_by_ts[expiry] / open_by_ts[entry]))
        predicted = _scalar_float(forecast["forecast"], "forecast")
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
            "forecast": predicted,
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



def summarize_scored_events(events: list[dict], minimum_per_horizon: int = 200) -> dict:
    """Summarize only genuinely matured, non-invalidated prospective ledger forecasts."""
    scored_ids = {
        row.get("forecast_id") for row in events
        if row.get("event_type") == "SCORE"
    }
    invalidated_ids = {
        row.get("forecast_id") for row in events
        if row.get("event_type") == "INVALIDATION"
    }
    forecasts = {
        row.get("forecast_id"): row for row in events
        if row.get("event_type") == "FORECAST"
    }
    rows_by_horizon: dict[str, list[dict]] = {}
    for score in events:
        if score.get("event_type") != "SCORE":
            continue
        forecast_id = score.get("forecast_id")
        if forecast_id not in scored_ids or forecast_id in invalidated_ids:
            continue
        forecast = forecasts.get(forecast_id)
        if forecast is None:
            continue
        try:
            actual = float(score["realized_outcome"])
            ridge = _scalar_float(forecast["forecast"], "forecast")
            benchmarks = json.loads(forecast.get("benchmark_forecasts") or "{}")
            if not np.isfinite([actual, ridge]).all():
                continue
            row = {"actual": actual, "ridge": ridge}
            for key, value in benchmarks.items():
                number = float(value)
                if np.isfinite(number):
                    row[key] = number
            rows_by_horizon.setdefault(str(int(score["horizon"])), []).append(row)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue

    result = {}
    for horizon, rows in rows_by_horizon.items():
        actual = np.asarray([row["actual"] for row in rows], dtype=float)
        block = {"n": len(rows), "minimum_for_probabilistic_claims": minimum_per_horizon,
                 "sample_gate": "MET" if len(rows) >= minimum_per_horizon else "NOT_MET",
                 "models": {}}
        for model, key in (("ridge", "ridge"), ("zero", "zero_return"),
                           ("drift", "training_drift"), ("momentum", "fixed_momentum")):
            if not all(key in row for row in rows):
                continue
            prediction = np.asarray([row[key] for row in rows], dtype=float)
            error = prediction - actual
            block["models"][model] = {
                "mae": float(np.mean(np.abs(error))),
                "rmse": float(np.sqrt(np.mean(error ** 2))),
                "mean_error": float(np.mean(error)),
                "directional_accuracy": (
                    None if model == "zero"
                    else float(np.mean(np.sign(prediction) == np.sign(actual)))
                ),
            }
        if "ridge" in block["models"] and "zero" in block["models"]:
            ridge_mae = block["models"]["ridge"]["mae"]
            zero_mae = block["models"]["zero"]["mae"]
            block["ridge_mae_difference_vs_zero"] = ridge_mae - zero_mae
            block["ridge_relative_mae_lift_vs_zero"] = (
                1.0 - ridge_mae / zero_mae if zero_mae > 0 else None
            )
        result[horizon] = block
    return {
        "source": "append-only prospective forecast ledger; matured SCORE events only",
        "probability_calibration_claim_allowed": False,
        "minimum_per_horizon": minimum_per_horizon,
        "by_horizon": result,
        "decision": "INSUFFICIENT_PROSPECTIVE_EVIDENCE" if not result or any(
            block["sample_gate"] != "MET" for block in result.values()
        ) else "SAMPLE_GATE_MET_REQUIRES_SEPARATE_CALIBRATION_AND_COST_TESTS",
    }

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
