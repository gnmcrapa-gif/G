import numpy as np
import pandas as pd

from btc_quant.ohlcv_challenger import (
    HISTORICAL_HOLDOUT_START_UTC,
    generate_ohlcv_forecast_events,
    make_ohlcv_features,
)


def _sample_frame(n=1900):
    end = pd.Timestamp("2026-11-16T00:00:00Z")
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 30000.0 * np.exp(np.cumsum(0.0001 + 0.005 * np.sin(t / 21.0)))
    open_price = close * (1.0 + 0.001 * np.cos(t / 13.0))
    volume = 1000.0 + 250.0 * np.sin(t / 9.0) + 30.0 * np.cos(t / 3.0)
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close,
        "volume": volume,
    })


def test_ohlcv_features_use_only_current_and_past_bars():
    frame = _sample_frame()
    first = make_ohlcv_features(frame)
    changed = frame.copy()
    changed.loc[len(changed) - 1, "volume"] *= 1000.0
    changed.loc[len(changed) - 1, "close"] *= 1.5
    second = make_ohlcv_features(changed)
    pd.testing.assert_frame_equal(first.iloc[:-1], second.iloc[:-1])


def test_ohlcv_challenger_emits_scalar_future_forecasts_without_holdout_training():
    frame = _sample_frame()
    now = pd.Timestamp("2026-11-17T19:00:00Z").to_pydatetime()
    events = generate_ohlcv_forecast_events(
        frame, "manifest-hash", "test-commit", now=now
    )
    assert {event["horizon"] for event in events} == {1, 3, 7, 30}
    for event in events:
        assert isinstance(event["forecast"], float)
        assert event["model_version"].startswith("ohlcv-challenger-0.1")
        assert pd.Timestamp(event["issued_at_utc"]) < pd.Timestamp(event["entry_timestamp_utc"])
        assert event["target"] == "log(Open[t+h+2]/Open[t+2])"
        note = event["notes"]
        cutoff = pd.Timestamp(note.split("training_cutoff_utc=")[1].split(";")[0])
        assert cutoff < HISTORICAL_HOLDOUT_START_UTC
        assert "historical holdout excluded from training and tuning" in note


def test_ohlcv_challenger_does_not_emit_if_holdout_history_is_unavailable():
    frame = _sample_frame(500)
    events = generate_ohlcv_forecast_events(
        frame, "manifest-hash", "test-commit",
        min_train_rows=100, now=pd.Timestamp("2026-11-17T19:00:00Z").to_pydatetime(),
    )
    assert events == []
