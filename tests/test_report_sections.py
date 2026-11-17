import pytest

from btc_quant.reporting import _build_longitudinal_comparison, _build_report_sections


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
