import io
import zipfile

from btc_quant.acquisition import _parse_binance_zip, _save_raw


def test_parse_binance_zip_preserves_venue_ohlcv_schema():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("klines.csv", "1704067200000,42000,43000,41000,42500,12\n")
    frame = _parse_binance_zip(content.getvalue())
    assert list(frame.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert frame.iloc[0]["close"] == 42500


def test_parse_binance_zip_supports_microsecond_timestamps():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("klines.csv", "1704067200000000,42000,43000,41000,42500,12\n")
    frame = _parse_binance_zip(content.getvalue())
    assert frame.iloc[0]["timestamp"].isoformat() == "2024-01-01T00:00:00+00:00"


def test_raw_manifest_records_schema_grade_and_terms(tmp_path):
    record = _save_raw(
        tmp_path, "sample.json", b"{}",
        "https://example.invalid/sample", "Test public source",
        "TestVenue", "BTC-USD", "USD", source_grade="B",
    )
    assert record["schema_version"] == "1.0"
    assert record["source_grade"] == "B"
    assert "provider terms apply" in record["license_terms_note"]
    assert record["size_bytes"] == 2



def test_raw_snapshots_are_immutable_when_provider_revises_same_filename(tmp_path):
    first = _save_raw(
        tmp_path, "same.json", b"first",
        "https://example.invalid/same", "Test source", "Venue", "BTC-USD", "USD",
    )
    second = _save_raw(
        tmp_path, "same.json", b"second",
        "https://example.invalid/same", "Test source", "Venue", "BTC-USD", "USD",
    )
    repeated = _save_raw(
        tmp_path, "same.json", b"second",
        "https://example.invalid/same", "Test source", "Venue", "BTC-USD", "USD",
    )
    first_path = tmp_path / first["file"]
    second_path = tmp_path / second["file"]
    assert first_path.read_bytes() == b"first"
    assert second_path.read_bytes() == b"second"
    assert first["file"] != second["file"]
    assert second["file"] == repeated["file"]
    assert second["content_addressed"] is True
