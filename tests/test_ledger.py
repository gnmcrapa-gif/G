import numpy as np
import pandas as pd
import pytest

from btc_quant.ledger import (
    generate_forecast_events,
    invalidate_late_forecasts,
    score_matured_events,
    summarize_scored_events,
)


def test_forecast_ledger_uses_validation_selected_alpha_by_horizon():
    n = 1200
    end = pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 30000.0 * np.exp(np.cumsum(0.0001 + 0.006 * np.sin(t / 19.0)))
    open_price = close * (1.0 + 0.001 * np.cos(t / 11.0))
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close,
        "volume": np.full(n, 100.0),
    })
    alphas = {1: 100.0, 3: 10.0, 7: 1.0, 30: 0.1}
    events = generate_forecast_events(
        frame, "manifest-hash", "test-commit",
        min_train_rows=100, ridge_alpha_by_horizon=alphas,
    )
    assert {event["horizon"] for event in events} == {1, 3, 7, 30}
    for event in events:
        alpha = alphas[event["horizon"]]
        assert f"alpha-{alpha:g}" in event["model_version"]
        assert f"alpha={alpha:g}" in event["notes"]
        assert pd.Timestamp(event["entry_timestamp_utc"]) > pd.Timestamp(event["issued_at_utc"])
        assert isinstance(event["forecast"], float)
        assert event["target"] == "log(Open[t+h+2]/Open[t+2])"
        assert pd.Timestamp(event["entry_timestamp_utc"]) == pd.Timestamp(event["signal_timestamp_utc"]) + pd.Timedelta(days=2)


def test_late_forecast_is_invalidated_not_deleted():
    n = 1200
    end = pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 30000.0 * np.exp(np.cumsum(0.0001 + 0.006 * np.sin(t / 19.0)))
    open_price = close * (1.0 + 0.001 * np.cos(t / 11.0))
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close,
        "volume": np.full(n, 100.0),
    })
    event = generate_forecast_events(
        frame, "manifest-hash", "test-commit",
        min_train_rows=100, ridge_alpha_by_horizon={1: 100.0, 3: 100.0, 7: 100.0, 30: 100.0},
    )[0]
    event["entry_timestamp_utc"] = (pd.Timestamp(event["issued_at_utc"]) - pd.Timedelta(hours=1)).isoformat()
    invalidations = invalidate_late_forecasts([event])
    assert len(invalidations) == 1
    assert invalidations[0]["event_type"] == "INVALIDATION"
    assert invalidations[0]["forecast_id"] == event["forecast_id"]


def test_prospective_ledger_summary_uses_only_matured_scored_events():
    import json

    forecast = {
        "event_type": "FORECAST", "forecast_id": "f1", "horizon": 1,
        "forecast": 0.02,
        "benchmark_forecasts": json.dumps({
            "zero_return": 0.0, "training_drift": 0.01, "fixed_momentum": -0.01,
        }),
    }
    score = {
        "event_type": "SCORE", "forecast_id": "f1", "horizon": "1",
        "realized_outcome": "0.01",
    }
    pending = {"event_type": "FORECAST", "forecast_id": "f2", "horizon": 1}
    invalidation = {"event_type": "INVALIDATION", "forecast_id": "f3"}
    result = summarize_scored_events([forecast, score, pending, invalidation])
    block = result["by_horizon"]["1"]
    assert block["n"] == 1
    assert block["models"]["ridge"]["mae"] == 0.01
    assert block["models"]["zero"]["mae"] == 0.01
    assert block["sample_gate"] == "NOT_MET"
    assert result["probability_calibration_claim_allowed"] is False



def test_legacy_array_encoded_forecast_is_scored_without_mutating_history():
    forecast = {
        "event_id": "forecast-old", "event_type": "FORECAST", "forecast_id": "old",
        "issued_at_utc": "2026-11-15T18:00:00+00:00",
        "model_version": "ridge-challenger-0.3", "code_commit": "old",
        "data_manifest_sha256": "old-hash", "target": "log(Open[t+h+2]/Open[t+2])",
        "horizon": 1, "signal_timestamp_utc": "2026-11-15T00:00:00+00:00",
        "feature_cutoff_utc": "2026-11-16T00:00:00+00:00", "regime_ex_ante": "range",
        "forecast": "[-0.01]",
        "benchmark_forecasts": '{"zero_return": 0.0, "training_drift": 0.001, "fixed_momentum": -0.002}',
        "entry_timestamp_utc": "2026-11-17T00:00:00+00:00",
        "expiry_timestamp_utc": "2026-11-18T00:00:00+00:00",
    }
    frame = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-11-17T00:00:00Z", "2026-11-18T00:00:00Z"]),
        "open": [100.0, 110.0],
    })
    scores = score_matured_events([forecast], frame)
    assert len(scores) == 1
    assert scores[0]["forecast"] == -0.01
    assert scores[0]["realized_outcome"] == pytest.approx(np.log(1.1))
    assert forecast["forecast"] == "[-0.01]"  # append-only historical record remains unchanged


def test_prospective_summary_accepts_legacy_singleton_array_forecast():
    forecast = {
        "event_type": "FORECAST", "forecast_id": "legacy", "horizon": 1,
        "forecast": "[-0.01]",
        "benchmark_forecasts": '{"zero_return": 0.0, "training_drift": 0.001, "fixed_momentum": -0.002}',
    }
    score = {"event_type": "SCORE", "forecast_id": "legacy", "horizon": "1",
             "realized_outcome": "0.02"}
    result = summarize_scored_events([forecast, score])
    assert result["by_horizon"]["1"]["n"] == 1
    assert result["by_horizon"]["1"]["models"]["ridge"]["mae"] == pytest.approx(0.03)
