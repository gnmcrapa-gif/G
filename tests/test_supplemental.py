from btc_quant.supplemental import (
    FRED_SERIES,
    _find_etf_sessions,
    _float_or_none,
    _parse_deribit_instrument,
    empty_supplemental_coverage,
    _pct_change,
)


def test_deribit_option_instrument_parser_extracts_expiry_strike_and_side():
    assert _parse_deribit_instrument("BTC-27NOV26-70000-C") == ("2026-11-27", 70000.0, "C")
    assert _parse_deribit_instrument("BTC-27NOV26-65000-P") == ("2026-11-27", 65000.0, "P")
    assert _parse_deribit_instrument("BTC-PERPETUAL") is None
    assert _parse_deribit_instrument("BTC-27NOV26-invalid-C") is None


def test_etf_session_extractor_selects_full_history_not_recent_preview():
    preview = [
        {"date": f"2026-11-{day:02d}", "netFlowUsd": float(day)}
        for day in range(10, 15)
    ]
    full = [
        {"date": f"2026-10-{day:02d}", "netFlowUsd": float(day)}
        for day in range(1, 22)
    ]
    payload = {
        "recentSessions": preview,
        "historical": {"sessions": full},
    }
    assert _find_etf_sessions(payload) == full


def test_numeric_helpers_reject_nonfinite_and_zero_denominator():
    assert _float_or_none("12.5") == 12.5
    assert _float_or_none("not-a-number") is None
    assert _float_or_none("nan") is None
    assert _pct_change(100.0, 110.0) == 10.0
    assert _pct_change(0.0, 110.0) is None
    assert _pct_change(None, 110.0) is None


def test_macro_series_have_units_frequencies_and_freshness_limits():
    assert FRED_SERIES["DGS10"]["unit"] == "percent"
    assert FRED_SERIES["DFII10"]["max_age_days"] == 5
    assert "not ICE DXY" in FRED_SERIES["DTWEXBGS"]["label"]
    assert FRED_SERIES["CPIAUCSL"]["lookback_days"] >= 365



def test_every_market_domain_has_an_explicit_default_not_run_or_unavailable_status():
    coverage = empty_supplemental_coverage()
    expected = {
        "spot_ohlcv", "spot_live_quotes", "per_exchange_derivatives", "options",
        "us_spot_etf_flows", "global_etp_flows", "exchange_flows_and_reserves",
        "liquidations", "macro_and_indices", "spot_futures_cvd",
        "geopolitical_regulatory_news",
    }
    assert set(coverage) == expected
    assert all(item.get("status") for item in coverage.values())
    assert coverage["exchange_flows_and_reserves"]["status"] == "UNAVAILABLE"
    assert coverage["spot_futures_cvd"]["status"] == "PROXY_ONLY"
