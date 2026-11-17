import pytest

from btc_quant.supplemental import (
    FRED_SERIES,
    _find_etf_sessions,
    _float_or_none,
    _news_keyword_tags,
    _parse_deribit_instrument,
    _parse_rss_articles,
    _pct_change,
    _summarize_hourly_taker_delta,
    empty_supplemental_coverage,
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
    assert _pct_change(100.0, 110.0) == pytest.approx(10.0)
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
    assert coverage["spot_futures_cvd"]["status"] == "NOT_RUN"



def test_hourly_taker_delta_calculates_exact_24h_7d_and_30d_windows():
    import time

    now_ms = int(time.time() * 1000)
    start_ms = now_ms - 900 * 60 * 60 * 1000
    rows = []
    for index in range(721):
        open_time = start_ms + index * 60 * 60 * 1000
        rows.append([
            open_time, "100", "110", "90", "105", "10",
            open_time + 3_599_999, "1000", 100, "6", "600", "0",
        ])
    result = _summarize_hourly_taker_delta(rows)
    assert result["status"] == "PASS"
    assert result["24h"]["cumulative_delta_btc"] == pytest.approx(48.0)
    assert result["7d"]["cumulative_delta_btc"] == pytest.approx(336.0)
    assert result["30d"]["cumulative_delta_btc"] == pytest.approx(1440.0)
    assert result["30d"]["delta_pct_of_total_volume"] == pytest.approx(20.0)



def test_official_rss_parser_keeps_publication_time_source_and_url():
    xml = b"""<?xml version="1.0"?>
    <rss><channel><item>
      <title>SEC publishes digital asset rule proposal</title>
      <link>https://www.sec.gov/example</link>
      <pubDate>Tue, 17 Nov 2026 16:00:00 GMT</pubDate>
      <description>Commission notice and comment period.</description>
    </item></channel></rss>"""
    articles = _parse_rss_articles(xml, "SEC")
    assert len(articles) == 1
    assert articles[0]["source"] == "SEC"
    assert articles[0]["url"] == "https://www.sec.gov/example"
    assert articles[0]["published_at_utc"] == "2026-11-17T16:00:00+00:00"
    assert "regulatory" in _news_keyword_tags(articles[0]["title"], articles[0]["snippet"])
    assert "crypto" not in _news_keyword_tags("Treasury announces new sanctions")


def test_news_keyword_tags_are_explicitly_rule_based():
    tags = _news_keyword_tags("Federal Reserve signals rates amid Bitcoin ETF flows")
    assert tags == ["macro_monetary", "crypto"]

def test_news_tags_use_whole_words_and_exclude_generic_policy_headlines():
    assert _news_keyword_tags("President Trump’s Immigration Policies Are Saving American Lives") == []
    assert _news_keyword_tags("The SEC announces a new digital asset rule") == ["regulatory", "crypto"]
    assert _news_keyword_tags("The second-quarter report is released") == []


def test_fred_session_retries_transient_http_failures_with_bounded_policy():
    import requests

    from btc_quant.supplemental import _configure_fred_session

    session = _configure_fred_session(requests.Session())
    adapter = session.get_adapter("https://")
    retry = adapter.max_retries
    assert retry.total == 2
    assert retry.connect == 2
    assert retry.read == 1
    assert retry.status == 2
    assert retry.status_forcelist == (429, 500, 502, 503, 504)
    assert retry.allowed_methods == frozenset({"GET"})
    session.close()
