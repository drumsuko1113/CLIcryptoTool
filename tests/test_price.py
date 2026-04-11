"""価格取得モジュールのテスト"""
from unittest.mock import patch, MagicMock
from src.price import (
    fetch_eth_usdt_ticker,
    fetch_usd_jpy_rate,
    get_eth_prices,
    format_price_display,
)


def _mock_binance_response():
    """Binance APIのモックレスポンス"""
    return {
        "symbol": "ETHUSDT",
        "lastPrice": "2500.50",
        "highPrice": "2600.00",
        "lowPrice": "2400.00",
        "volume": "123456.789",
        "quoteVolume": "308641975.00",
        "priceChangePercent": "2.35",
    }


def _mock_rate_response():
    """為替レートのモックレスポンス"""
    return {"rates": {"JPY": 155.50}}


class TestFetchEthUsdtTicker:
    def test_returns_ticker_data(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _mock_binance_response()

        with patch("src.price.requests.get", return_value=mock_resp):
            result = fetch_eth_usdt_ticker()

        assert result["lastPrice"] == "2500.50"
        assert result["highPrice"] == "2600.00"
        assert result["lowPrice"] == "2400.00"

    def test_returns_none_on_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("Server Error")

        with patch("src.price.requests.get", return_value=mock_resp):
            result = fetch_eth_usdt_ticker()

        assert result is None


class TestFetchUsdJpyRate:
    def test_returns_rate(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _mock_rate_response()

        with patch("src.price.requests.get", return_value=mock_resp):
            result = fetch_usd_jpy_rate()

        assert result == 155.50

    def test_returns_none_on_error(self):
        with patch("src.price.requests.get", side_effect=Exception("Network")):
            result = fetch_usd_jpy_rate()

        assert result is None


class TestGetEthPrices:
    def test_combines_data(self):
        ticker = _mock_binance_response()
        rate = 155.50

        with patch("src.price.fetch_eth_usdt_ticker", return_value=ticker), \
             patch("src.price.fetch_usd_jpy_rate", return_value=rate):
            result = get_eth_prices()

        assert result is not None
        assert result["eth_usd"] == 2500.50
        assert result["eth_jpy"] == 2500.50 * 155.50
        assert result["high_usd"] == 2600.00
        assert result["low_usd"] == 2400.00
        assert result["change_percent"] == 2.35

    def test_returns_none_when_ticker_fails(self):
        with patch("src.price.fetch_eth_usdt_ticker", return_value=None), \
             patch("src.price.fetch_usd_jpy_rate", return_value=155.50):
            result = get_eth_prices()

        assert result is None


class TestFormatPriceDisplay:
    def test_formats_correctly(self):
        prices = {
            "eth_usd": 2500.50,
            "eth_jpy": 388827.75,
            "high_usd": 2600.00,
            "low_usd": 2400.00,
            "high_jpy": 404300.00,
            "low_jpy": 373200.00,
            "volume": 123456.789,
            "change_percent": 2.35,
            "usd_jpy_rate": 155.50,
        }
        output = format_price_display(prices)
        assert "ETH/USD" in output
        assert "ETH/JPY" in output
        assert "2,500.50" in output
        assert "24H" in output
