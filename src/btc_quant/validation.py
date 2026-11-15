"""Small deterministic primitives; these do not download data or fit models."""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_OHLCV = ("timestamp", "open", "high", "low", "close", "volume")


class DataValidationError(ValueError):
    """Raised when a market-data invariant fails."""


def validate_ohlcv(frame: pd.DataFrame) -> dict[str, int]:
    """Validate canonical OHLCV rows; do not silently repair or drop records."""
    missing_columns = [column for column in REQUIRED_OHLCV if column not in frame.columns]
    if missing_columns:
        raise DataValidationError(f"missing columns: {missing_columns}")
    if frame.empty:
        raise DataValidationError("dataset is empty")

    ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if ts.isna().any():
        raise DataValidationError("unparseable timestamps")
    if ts.duplicated().any():
        raise DataValidationError("duplicate timestamps")
    if not ts.is_monotonic_increasing:
        raise DataValidationError("timestamps are not strictly increasing")

    prices = frame[["open", "high", "low", "close"]].to_numpy(dtype=float)
    volume = frame["volume"].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise DataValidationError("prices must be finite and positive")
    if not np.isfinite(volume).all() or (volume < 0).any():
        raise DataValidationError("volume must be finite and non-negative")

    o, h, l, c = (frame[column].to_numpy(dtype=float) for column in ("open", "high", "low", "close"))
    if (h < np.maximum.reduce([o, l, c])).any():
        raise DataValidationError("high violates OHLC invariant")
    if (l > np.minimum.reduce([o, h, c])).any():
        raise DataValidationError("low violates OHLC invariant")

    return {
        "rows": len(frame),
        "duplicates": int(ts.duplicated().sum()),
        "missing_volume": int(frame["volume"].isna().sum()),
    }


def forward_open_log_return(open_prices: pd.Series, horizon: int) -> pd.Series:
    """Return log(Open[t+h+1] / Open[t+1]) indexed at signal time t."""
    if horizon not in (1, 3, 7, 30):
        raise ValueError("horizon must be one of 1, 3, 7, 30")
    values = pd.to_numeric(open_prices, errors="coerce").astype(float)
    if (values.dropna() <= 0).any():
        raise DataValidationError("open prices must be positive")
    shifted_entry = values.shift(-1)
    shifted_exit = values.shift(-(horizon + 1))
    return np.log(shifted_exit / shifted_entry).rename(f"target_h{horizon}")
