"""Strict OHLCV and daily-cadence validation."""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_OHLCV = ("timestamp", "open", "high", "low", "close", "volume")
# The daily job runs at 16:00 UTC, after Open[t+1] has already occurred.
EXECUTION_ENTRY_LAG_SESSIONS = 2


class DataValidationError(ValueError):
    """Raised when a market-data invariant fails."""


def validate_ohlcv(frame: pd.DataFrame, *, require_daily: bool = True,
                   require_closed: bool = True, now: pd.Timestamp | None = None,
                   allow_stale: bool = False) -> dict[str, int | float | str | None]:
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
    stale_error = (
        f"stale daily data; latest candle age={latest_age}"
        if latest_age > pd.Timedelta(days=1) else None
    )
    if stale_error and not allow_stale:
        raise DataValidationError(stale_error)

    close_returns = np.abs(np.diff(np.log(c)))
    intraday_range_pct = (h - l) / o
    volume_median = float(np.median(volume))
    volume_series = pd.Series(volume, dtype=float)
    prior_volume = volume_series.shift(1)
    prior_median = prior_volume.rolling(window=90, min_periods=60).median()
    prior_mad = prior_volume.rolling(window=90, min_periods=60).apply(
        lambda values: float(np.median(np.abs(values - np.median(values)))),
        raw=True,
    )
    robust_scale = 1.4826 * prior_mad
    rolling_robust_z = (volume_series - prior_median).abs() / robust_scale.where(robust_scale > 0)
    valid_robust_z = rolling_robust_z.replace([np.inf, -np.inf], np.nan).dropna()
    robust_volume_z_max = float(valid_robust_z.max()) if not valid_robust_z.empty else None
    robust_volume_z_index = int(valid_robust_z.idxmax()) if not valid_robust_z.empty else None
    volume_max_index = int(np.argmax(volume))
    close_return_max_index = int(np.argmax(close_returns)) + 1 if len(close_returns) else 0
    intraday_range_max_index = int(np.argmax(intraday_range_pct))
    candle_close_utc = ts.max() + pd.Timedelta(days=1)
    exact_age_hours = max(0.0, (current - candle_close_utc).total_seconds() / 3600.0)
    return {
        "rows": len(frame), "duplicates": 0, "missing_volume": 0,
        "first_timestamp_utc": ts.min().isoformat(),
        "last_timestamp_utc": ts.max().isoformat(),
        "gap_count": 0, "closed_candles_only": "PASS",
        "latest_age_days": int(latest_age / pd.Timedelta(days=1)),
        "latest_candle_age_hours": round(exact_age_hours, 3),
        "freshness_status": "FAIL" if stale_error else "PASS",
        "freshness_error": stale_error,
        "zero_volume_rows": int(np.count_nonzero(volume == 0)),
        "zero_volume_pct": float(np.mean(volume == 0) * 100.0),
        "volume_median_btc": volume_median,
        "volume_median_scope": "full available history; descriptive only",
        "volume_robust_z_window_sessions": 90,
        "volume_robust_z_min_history_sessions": 60,
        "volume_robust_z_scope": "current volume versus median and MAD of the prior 90 completed daily sessions; current session excluded",
        "volume_p99_btc": float(np.quantile(volume, 0.99)),
        "volume_max_btc": float(np.max(volume)),
        "volume_robust_z_max": robust_volume_z_max,
        "volume_robust_z_max_timestamp_utc": (
            ts.iloc[robust_volume_z_index].isoformat() if robust_volume_z_index is not None else None
        ),
        "volume_robust_z_max_prior_median_btc": (
            float(prior_median.iloc[robust_volume_z_index]) if robust_volume_z_index is not None else None
        ),
        "volume_robust_z_max_prior_mad_btc": (
            float(prior_mad.iloc[robust_volume_z_index]) if robust_volume_z_index is not None else None
        ),
        "volume_max_timestamp_utc": ts.iloc[volume_max_index].isoformat(),
        "absolute_close_return_max_timestamp_utc": ts.iloc[close_return_max_index].isoformat(),
        "intraday_range_pct_max_timestamp_utc": ts.iloc[intraday_range_max_index].isoformat(),
        "absolute_close_return_p99": float(np.quantile(close_returns, 0.99)) if len(close_returns) else 0.0,
        "absolute_close_return_max": float(np.max(close_returns)) if len(close_returns) else 0.0,
        "intraday_range_pct_p99": float(np.quantile(intraday_range_pct, 0.99)),
        "intraday_range_pct_max": float(np.max(intraday_range_pct)),
        "diagnostic_note": "Zero-volume and tail metrics are descriptive QA diagnostics, not automatic rejection thresholds.",
    }


def forward_open_log_return(
    open_prices: pd.Series, horizon: int, *, entry_lag_sessions: int = EXECUTION_ENTRY_LAG_SESSIONS
) -> pd.Series:
    """Return log(Open[t+entry_lag+h]/Open[t+entry_lag]).

    Lag 1 is the theoretical next-open target, but it is not executable by the
    16:00 UTC daily job because Open[t+1] has already occurred at issuance.
    Production defaults to lag 2, reserving one complete daily bar for latency.
    """
    if horizon not in (1, 3, 7, 30):
        raise ValueError("horizon must be one of 1, 3, 7, 30")
    if (isinstance(entry_lag_sessions, bool)
            or not isinstance(entry_lag_sessions, int)
            or entry_lag_sessions < 1):
        raise ValueError("entry_lag_sessions must be a positive integer")
    values = pd.to_numeric(open_prices, errors="coerce").astype(float)
    if (values.dropna() <= 0).any():
        raise DataValidationError("open prices must be positive")
    return np.log(
        values.shift(-(horizon + entry_lag_sessions))
        / values.shift(-entry_lag_sessions)
    ).rename(f"target_h{horizon}_entrylag{entry_lag_sessions}")
