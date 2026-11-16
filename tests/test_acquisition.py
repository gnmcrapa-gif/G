import io
import zipfile

from btc_quant.acquisition import _parse_binance_zip


def test_parse_binance_zip_preserves_venue_ohlcv_schema():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("klines.csv", "1704067200000,42000,43000,41000,42500,12\n")
    frame = _parse_binance_zip(content.getvalue())
    assert list(frame.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert frame.iloc[0]["close"] == 42500
