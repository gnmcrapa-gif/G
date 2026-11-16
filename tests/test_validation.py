import numpy as np
import pandas as pd
import pytest

from btc_quant.validation import DataValidationError, forward_open_log_return, validate_ohlcv


def sample_frame():
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC"),
        "open": [100.0, 101.0, 102.0], "high": [102.0, 103.0, 104.0],
        "low": [99.0, 100.0, 101.0], "close": [101.0, 102.0, 103.0],
        "volume": [10.0, 11.0, 12.0],
    })


def test_valid_ohlcv_passes():
    now = pd.Timestamp("2024-01-04T12:00:00Z")
    assert validate_ohlcv(sample_frame(), now=now)["rows"] == 3


def test_duplicate_timestamps_fail():
    frame = sample_frame()
    frame.loc[2, "timestamp"] = frame.loc[1, "timestamp"]
    with pytest.raises(DataValidationError, match="duplicate"):
        validate_ohlcv(frame)


def test_invalid_high_fails():
    frame = sample_frame()
    frame.loc[0, "high"] = 98.0
    with pytest.raises(DataValidationError, match="high"):
        validate_ohlcv(frame)


def test_daily_gap_fails():
    frame = sample_frame().drop(index=1).reset_index(drop=True)
    with pytest.raises(DataValidationError, match="gap"):
        validate_ohlcv(frame)


def test_non_midnight_daily_timestamp_fails():
    frame = sample_frame()
    frame.loc[1, "timestamp"] += pd.Timedelta(hours=1)
    with pytest.raises(DataValidationError, match="00:00 UTC"):
        validate_ohlcv(frame)


def test_incomplete_current_day_fails():
    frame = sample_frame()
    now = pd.Timestamp("2024-01-04T12:00:00Z")
    frame.loc[2, "timestamp"] = pd.Timestamp("2024-01-04T00:00:00Z")
    with pytest.raises(DataValidationError, match="current or future"):
        validate_ohlcv(frame, now=now)


def test_target_alignment_matches_next_open_to_future_open():
    opens = pd.Series([100.0, 110.0, 121.0, 133.1, 146.41])
    target = forward_open_log_return(opens, horizon=1)
    assert target.iloc[0] == pytest.approx(np.log(133.1 / 121.0))
    assert target.iloc[-3:].isna().all()


def test_non_positive_open_fails():
    with pytest.raises(DataValidationError, match="positive"):
        forward_open_log_return(pd.Series([100.0, 0.0, 110.0]), horizon=1)
