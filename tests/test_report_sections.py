import pytest

from btc_quant.reporting import (
    _build_longitudinal_comparison,
    _build_report_sections,
    _market_snapshot,
    render_markdown_report,
)
import pandas as pd


def _scores(start="2025-11-17", end="2026-11-16", mae=0.01):
    return {
        "holdout_start_utc": start,
        "holdout_end_utc": end,
        "holdout_metrics": {
            str(h): {"zero": {"mae": mae}, "ridge": {"mae": mae + 0.001}}
            for h in (1, 3, 7, 30)
        },
    }


def test_longitudinal_comparison_only_compares_same_venue_quote_and_window():
    previous = {
        "started_at_utc": "2026-11-16T19:00:00+00:00",
        "finished_at_utc": "2026-11-16T19:01:00+00:00",
        "status": "COMPLETE_NOT_PROMOTED",
        "market_snapshot": {"venues": [{
            "venue": "Binance", "symbol": "BTCUSDT", "quote_currency": "USDT",
            "close_quote_per_btc": 65000.0,
        }]},
        "steps": [{"step": "walk_forward", "scores": _scores()}],
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 0}}},
    }
    current = {
        "status": "COMPLETE_NOT_PROMOTED",
        "market_snapshot": {"venues": [
            {
                "venue": "Binance", "symbol": "BTCUSDT", "quote_currency": "USDT",
                "close_quote_per_btc": 66000.0, "candle_open_timestamp_utc": "2026-11-16T00:00:00+00:00",
            },
            {
                "venue": "Bitstamp", "symbol": "BTC/USD", "quote_currency": "USD",
                "close_quote_per_btc": 65500.0,
            },
        ]},
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 2}}},
    }
    result = _build_longitudinal_comparison(previous, current, _scores())
    assert result["status"] == "COMPARISON_AVAILABLE"
    assert result["historical_benchmark_comparison"]["status"] == "COMPARABLE_SAME_HISTORICAL_CONTINUITY_WINDOW"
    assert result["historical_benchmark_comparison"]["zero_return_mae"]["1"]["difference_log_return_units"] == pytest.approx(0.0)
    assert result["same_venue_price_snapshots"][0]["close_change_since_previous_report_pct"] == pytest.approx(1000.0 / 65000.0 * 100.0)
    assert result["same_venue_price_snapshots"][1]["status"] == "NOT_COMPARABLE_NO_MATCHING_PRIOR_SNAPSHOT"
    assert result["prospective_matured_counts"]["1"] == {"previous_matured": 0, "current_matured": 2}


def test_longitudinal_comparison_refuses_different_holdout_windows():
    previous = {"steps": [{"step": "walk_forward", "scores": _scores()}]}
    result = _build_longitudinal_comparison(previous, {}, _scores(start="2025-12-01"))
    assert result["historical_benchmark_comparison"]["status"] == "NOT_COMPARABLE_DIFFERENT_OR_MISSING_HOLDOUT_WINDOW"


def test_report_sections_keep_cost_backtest_blocked_without_prospective_sample():
    run = {
        "steps": [],
        "prospective_ledger_validation": {"by_horizon": {}},
        "ledger": {"forecast_events_created": 0, "score_events_created": 0},
        "market_snapshot": {"venues": [{
            "venue": "Binance", "close_change_1d_pct": 1.0, "intraday_range_pct": 2.0,
            "volume_vs_prior_30d_median": 1.5, "candle_open_timestamp_utc": "2026-11-16T00:00:00+00:00",
        }]},
    }
    taxonomy, economic, closing = _build_report_sections(run, _scores())
    assert set(taxonomy) == {"FACT", "INTERPRETATION", "HYPOTHESIS", "FORECAST"}
    assert economic["status"] == "BLOCKED_INSUFFICIENT_PROSPECTIVE_EVIDENCE"
    assert economic["cost_adjusted_strategy_backtest_executed"] is False
    assert len(closing["observed_drivers"]) == 3
    assert closing["single_next_priority_experiment"]



def test_market_snapshot_adds_7d_30d_and_technical_reference_levels():
    timestamps = pd.date_range("2026-01-01", periods=250, freq="D", tz="UTC")
    close = [100.0 + index for index in range(250)]
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close,
        "high": [value + 2.0 for value in close],
        "low": [value - 2.0 for value in close],
        "close": close,
        "volume": [1000.0] * 250,
    })
    snapshot = _market_snapshot(frame, "Binance", "BTCUSDT", "USDT", "2026-09-07T00:00:00+00:00")
    assert snapshot["close_change_7d_pct"] == pytest.approx((349.0 / 342.0 - 1.0) * 100.0)
    assert snapshot["close_change_30d_pct"] == pytest.approx((349.0 / 319.0 - 1.0) * 100.0)
    assert snapshot["sma_200_quote_per_btc"] is not None
    assert snapshot["high_20d_quote_per_btc"] == 351.0
    assert snapshot["low_20d_quote_per_btc"] == 328.0
    assert snapshot["atr_14_quote_per_btc"] == 4.0


def test_markdown_report_discloses_stale_and_unavailable_context_sources():
    report = render_markdown_report({
        "protocol": "V5.6",
        "status": "COMPLETE_NOT_PROMOTED",
        "started_at_utc": "2026-11-17T00:00:00+00:00",
        "supplemental_data": {
            "coverage": {
                "us_spot_etf_flows": {"status": "STALE", "reason": "two sessions behind"},
                "exchange_flows_and_reserves": {"status": "UNAVAILABLE", "reason": "no wallet labels"},
            },
            "spot_live": {"venues": {}},
        },
        "steps": [],
        "market_snapshot": {"venues": []},
        "ledger": {},
        "risk": {"mode": "paper_only", "live_trading_enabled": False, "theoretical_exposure_pct": 0},
        "pre_report_review": {"status": "PASS", "review_cycles": [], "blocking_failures": []},
        "closing_assessment": {},
    }, {})
    assert "us_spot_etf_flows" in report
    assert "STALE" in report
    assert "exchange_flows_and_reserves" in report
    assert "UNAVAILABLE" in report
