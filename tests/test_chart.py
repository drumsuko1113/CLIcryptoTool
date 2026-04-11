"""チャート・テクニカル指標モジュールのテスト"""
from unittest.mock import patch, MagicMock
from src.chart import (
    fetch_klines,
    calc_sma,
    calc_rsi,
    calc_macd,
)


def _sample_klines():
    """サンプルKlineデータ（20本）"""
    base = 2500.0
    klines = []
    for i in range(30):
        o = base + i * 10
        h = o + 20
        low = o - 10
        c = o + 5
        vol = 1000.0
        # Binance kline format: [open_time, open, high, low, close, volume, ...]
        klines.append([
            1700000000000 + i * 3600000,
            str(o), str(h), str(low), str(c), str(vol),
            1700000000000 + (i + 1) * 3600000 - 1,
            "0", "0", "0", "0", "0"
        ])
    return klines


class TestFetchKlines:
    def test_returns_kline_data(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _sample_klines()

        with patch("src.chart.requests.get", return_value=mock_resp):
            result = fetch_klines()

        assert len(result) == 30

    def test_returns_empty_on_error(self):
        with patch("src.chart.requests.get", side_effect=Exception("Error")):
            result = fetch_klines()

        assert result == []


class TestCalcSma:
    def test_sma_5(self):
        closes = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        result = calc_sma(closes, 5)
        assert len(result) == 6
        assert result[4] == 30.0  # (10+20+30+40+50)/5
        assert result[5] == 40.0  # (20+30+40+50+60)/5
        assert result[0] is None

    def test_sma_insufficient_data(self):
        closes = [10.0, 20.0]
        result = calc_sma(closes, 5)
        assert all(v is None for v in result)


class TestCalcRsi:
    def test_rsi_range(self):
        closes = [float(2500 + i * 10) for i in range(30)]
        result = calc_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0.0 <= v <= 100.0

    def test_rsi_uptrend(self):
        closes = [float(100 + i * 10) for i in range(30)]
        result = calc_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert valid[-1] > 50.0  # 上昇トレンドならRSI>50


class TestCalcMacd:
    def test_macd_returns_three_lists(self):
        closes = [float(2500 + i * 5) for i in range(50)]
        macd_line, signal, histogram = calc_macd(closes)
        assert len(macd_line) == 50
        assert len(signal) == 50
        assert len(histogram) == 50
