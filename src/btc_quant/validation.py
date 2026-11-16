"""Strict OHLCV and daily-cadence validation."""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_OHLCV = ("timestamp", "open", "high", "low", "close", "volume")


class DataValidationError(ValueError):
    """Raised when a market-data invariant fails."""


def validate_ohlcv(frame: pd.DataFrame, *, require_daily: bool = True,
                   require_closed: bool = True, now: pd.Timestamp | None = None) -> dict[str, int | str]:
    """Validate without silently repairing rows; timestamps represent UTC candle opens."""
    missing = [column for column in REQUIRED_OHLCV if column not in frame.columns]
    if missing:
        raise DataValidationError(f"missing columns: {missing}")
    if frame.empty:
        raise DataValidationError("dataset is empty")
    ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if ts.isna().any():
        raise DataValidationError("unparseable timestamps")
    if ts.duplicated().any():
        raise DataValidationError("duplicate timestamps")
    if not ts.is_monotonic_increasing:
        raise DataValidationError("timestamps are not strictly increasing")
    if require_daily:
        if not (ts == ts.dt.floor("D")).all():
            raise DataValidationError("daily candle timestamps must align to 00:00 UTC")
        gaps = ts.diff().dropna()
        if (gaps != pd.Timedelta(days=1)).any():
            missing_count = int((gaps / pd.Timedelta(days=1)).round().sub(1).clip(lower=0).sum())
            raise DataValidationError(f"daily cadence gap detected; missing_days={missing_count}")
    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now).tz_convert("UTC")
    if require_closed and (ts.dt.floor("D") >= current.floor("D")).any():
        raise DataValidationError("dataset contains current or future UTC daily candle")
    numeric = frame[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric, errors="coerce")
    values = numeric[["open", "high", "low", "close"]].to_numpy(dtype=float)
    volume = numeric["volume"].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise DataValidationError("prices must be finite and positive")
    if not np.isfinite(volume).all() or (volume < 0).any():
        raise DataValidationError("volume must be finite and non-negative")
    o, h, l, c = (numeric[col].to_numpy(dtype=float) for col in ("open", "high", "low", "close"))
    if (h < np.maximum.reduce([o, l, c])).any():
        raise DataValidationError("high violates OHLC invariant")
    if (l > np.minimum.reduce([o, h, c])).any():
        raise DataValidationError("low violates OHLC invariant")
    return {"rows": len(frame), "duplicates": 0, "missing_volume": 0,
            "first_timestamp_utc": ts.min().isoformat(), "last_timestamp_utc": ts.max().isoformat(),
            "gap_count": 0, "closed_candles_only": "PASS"}


def forward_open_log_return(open_prices: pd.Series, horizon: int) -> pd.Series:
    """Target y[t,h]=log(Open[t+h+1]/Open[t+1]); signal after close t."""
    if horizon not in (1, 3, 7, 30):
        raise ValueError("horizon must be one of 1, 3, 7, 30")
    values = pd.to_numeric(open_prices, errors="coerce").astype(float)
    if (values.dropna() <= 0).any():
        raise DataValidationError("open prices must be positive")
    return np.log(values.shift(-(horizon + 1)) / values.shift(-1)).rename(f"target_h{horizon}")
