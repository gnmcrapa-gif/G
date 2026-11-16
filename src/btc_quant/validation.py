"""Strict OHLCV and daily-cadence validation."""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_OHLCV = ("timestamp", "open", "high", "low", "close", "volume")


class DataValidationError(ValueError):
    """Raised when a market-data invariant fails."""


def validate_ohlcv(frame: pd.DataFrame, *, require_daily: bool = True,
                   require_closed: bool = True, now: pd.Timestamp | None = None) -> dict[str, int | str]:
    """Validate without repairing rows; input timestamps must explicitly be UTC-aware."""
    missing = [column for column in REQUIRED_OHLCV if column not in frame.columns]
    if missing:
        raise DataValidationError(f"missing columns: {missing}")
    if frame.empty:
        raise DataValidationError("dataset is empty")

    parsed = []
    for value in frame["timestamp"]:
        try:
            stamp = pd.Timestamp(value)
        except (TypeError, ValueError) as exc:
            raise DataValidationError(f"unparseable timestamp: {value!r}") from exc
        if pd.isna(stamp) or stamp.tzinfo is None:
            raise DataValidationError("timestamps must include an explicit UTC timezone")
        if stamp.utcoffset().total_seconds() != 0:
            raise DataValidationError("timestamps must be UTC; non-zero timezone offset found")
        parsed.append(stamp.tz_convert("UTC"))
    ts = pd.Series(pd.DatetimeIndex(parsed), index=frame.index)
    if ts.isna().any():
        raise DataValidationError("unparseable timestamps")
    if ts.duplicated().any():
        raise DataValidationError("duplicate timestamps")
    if not ts.is_monotonic_increasing:
        raise DataValidationError("timestamps are not strictly increasing")

    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if current.tzinfo is None:
        raise DataValidationError("validation 'now' must be timezone-aware")
    current = current.tz_convert("UTC")
    if require_closed and (ts.dt.floor("D") >= current.floor("D")).any():
        raise DataValidationError("dataset contains current or future UTC daily candle")
    if require_daily:
        if not (ts == ts.dt.floor("D")).all():
            raise DataValidationError("daily candle timestamps must align to 00:00 UTC")
        gaps = ts.diff().dropna()
        if (gaps != pd.Timedelta(days=1)).any():
            missing_count = int((gaps / pd.Timedelta(days=1)).round().sub(1).clip(lower=0).sum())
            raise DataValidationError(f"daily cadence gap detected; missing_days={missing_count}")

    numeric = frame[["open", "high", "low", "close", "volume"]].apply(
        pd.to_numeric, errors="coerce"
    )
    values = numeric[["open", "high", "low", "close"]].to_numpy(dtype=float)
    volume = numeric["volume"].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise DataValidationError("prices must be finite and positive")
    if not np.isfinite(volume).all() or (volume < 0).any():
        raise DataValidationError("volume must be finite and non-negative")
    o, h, l, c = (
        numeric[col].to_numpy(dtype=float) for col in ("open", "high", "low", "close")
    )
    if (h < np.maximum.reduce([o, l, c])).any():
        raise DataValidationError("high violates OHLC invariant")
    if (l > np.minimum.reduce([o, h, c])).any():
        raise DataValidationError("low violates OHLC invariant")

    latest_age = current.floor("D") - ts.max().floor("D")
    # Daily crypto trades every day. At a 16:00 UTC run, yesterday's close is
    # expected (age=1 day); two missing daily sessions must block research.
    if latest_age > pd.Timedelta(days=1):
        raise DataValidationError(f"stale daily data; latest candle age={latest_age}")
    return {
        "rows": len(frame), "duplicates": 0, "missing_volume": 0,
        "first_timestamp_utc": ts.min().isoformat(),
        "last_timestamp_utc": ts.max().isoformat(),
        "gap_count": 0, "closed_candles_only": "PASS",
        "latest_age_days": int(latest_age / pd.Timedelta(days=1)),
    }


def forward_open_log_return(open_prices: pd.Series, horizon: int) -> pd.Series:
    """Target after one full daily execution-latency bar: log(Open[t+h+2]/Open[t+2])."""
    if horizon not in (1, 3, 7, 30):
        raise ValueError("horizon must be one of 1, 3, 7, 30")
    values = pd.to_numeric(open_prices, errors="coerce").astype(float)
    if (values.dropna() <= 0).any():
        raise DataValidationError("open prices must be positive")
    return np.log(values.shift(-(horizon + 2)) / values.shift(-2)).rename(f"target_h{horizon}")
