from datetime import UTC, datetime, timedelta

import pytest

from btc_quant.supplemental import (
    FRED_SERIES,
    _ckh_series_summary,
    _contains_liquidation_data,
    _find_etf_sessions,
    _float_or_none,
    _news_keyword_tags,
    _parse_bitwise_weekly_flows,
    _parse_ckh_exchange_ranking,
    _parse_deribit_instrument,
    _parse_provider_money,
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



def test_bitwise_weekly_global_etp_parser_extracts_global_btc_and_us_spot_subset():
    html = b"""<html><head>
    <meta property="article:published_time" content="2026-11-16T08:00:00+00:00">
    </head><body><h1>Weekly Crypto Market Compass</h1>
    <p>Global crypto ETPs experienced around -1633.9 mn USD in net outflows last week,
    after -1779.4 mn USD in net outflows the previous week.</p>
    <p>Global Bitcoin ETPs experienced net outflows of -1112.7 mn USD last week,
    of which -1119.8 mn USD in net outflows were related to US spot Bitcoin ETFs.</p>
    </body></html>"""
    result = _parse_bitwise_weekly_flows(html, 2026, 47)
    assert result["report_week"] == "2026-W47"
    assert result["global_crypto_etp_weekly_flow_usd_mn"] == pytest.approx(-1633.9)
    assert result["global_bitcoin_etp_weekly_flow_usd_mn"] == pytest.approx(-1112.7)
    assert result["us_spot_bitcoin_etf_component_usd_mn"] == pytest.approx(-1119.8)
    assert result["non_us_bitcoin_etp_residual_usd_mn"] == pytest.approx(7.1)
    assert result["published_at_utc"] == "2026-11-16T08:00:00+00:00"
    assert result["status"] == "PASS"


def test_bitwise_weekly_parser_does_not_invent_missing_global_flows():
    html = b"<html><body><h1>Unrelated report</h1></body></html>"
    with pytest.raises(ValueError):
        _parse_bitwise_weekly_flows(html, 2026, 47)



def test_cryptokeyhole_series_requires_finality_and_rejects_preview_data():
    final_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    provisional_time = datetime.now(UTC).isoformat()
    payload = {
        "metric": "ckh.ExchangeNetflowVolumeBTC",
        "unit": "BTC",
        "source": "labeled exchange wallets",
        "method": "net inflow minus outflow",
        "points": [
            {"t": final_time, "v": "-120.5", "finality": "final"},
            {"t": provisional_time, "v": "30.0", "finality": "provisional"},
        ],
    }
    result = _ckh_series_summary(payload, None)
    assert result["status"] == "PASS"
    assert result["latest_final"]["value"] == pytest.approx(-120.5)
    assert result["unit"] == "BTC"
    preview = _ckh_series_summary(payload, "true")
    assert preview["status"] == "PREVIEW_ONLY"
    assert "latest_final" not in preview


def test_cryptokeyhole_liquidation_detection_is_nested_and_explicit():
    assert _contains_liquidation_data({"move": {"liquidations": {"long_usd": 123}}})
    assert not _contains_liquidation_data({"move": {"open_interest": 123}})



def test_cryptokeyhole_exchange_ranking_parses_daily_and_7d_aggregate_flows():
    html = b"""<html><body>
    <p>Daily ranking, UTC day 16 Nov 2026; updated 21:57 UTC on 17 Nov 2026.</p>
    <table>
      <tr><th>Exchange</th><th>Net flow</th><th>Net flow 7d</th><th>Coins covered</th></tr>
      <tr><td>Binance</td><td>−$377.2M</td><td>−$881.0M</td><td>Bitcoin, Ether, Stablecoins</td></tr>
      <tr><td>KuCoin</td><td>−$20.5M</td><td>+$36.7M</td><td>Bitcoin, Ether</td></tr>
      <tr><td>HTX</td><td>+$415.2K</td><td>−$14.1M</td><td>Bitcoin, Ether</td></tr>
      <tr><td>Bybit</td><td>+$27.0M</td><td>+$513.0M</td><td>Bitcoin, Ether</td></tr>
    </table>
    <h2>Events, last 30 days</h2>
    <ul><li>KuCoin: unusual net outflow (open): opened 17 Nov 2026, 07:00 UTC.</li></ul>
    <h2>Exchanges covered</h2>
    </body></html>"""
    result = _parse_ckh_exchange_ranking(html)
    assert result["status"] == "PASS"
    assert result["latest_complete_day_utc"] == "2026-11-16T00:00:00+00:00"
    assert result["page_updated_at_utc"] == "2026-11-17T21:57:00+00:00"
    flows = {row["exchange"]: row for row in result["exchanges"]}
    assert flows["Binance"]["daily_netflow_usd"] == pytest.approx(-377_200_000)
    assert flows["HTX"]["daily_netflow_usd"] == pytest.approx(415_200)
    assert flows["Bybit"]["netflow_7d_usd"] == pytest.approx(513_000_000)
    assert "Bitcoin" in flows["Binance"]["coins_covered"]
    assert "not BTC-only" in result["flow_scope"]


def test_cryptokeyhole_provider_money_parser_handles_sign_and_scale():
    assert _parse_provider_money("−$1.25B") == pytest.approx(-1_250_000_000)
    assert _parse_provider_money("+$77.7M") == pytest.approx(77_700_000)
    assert _parse_provider_money("+415.2K") == pytest.approx(415_200)
