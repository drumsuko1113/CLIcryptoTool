"""ルールベース分析モジュールのテスト"""
from src.analysis import analyze_market


class TestAnalyzeMarket:
    def test_returns_analysis_string(self):
        indicators = {
            "rsi": 75.0,
            "macd": 5.0,
            "signal": 3.0,
            "histogram": 2.0,
            "sma5": 2600.0,
            "sma13": 2550.0,
            "sma25": 2500.0,
            "current_price": 2650.0,
        }
        result = analyze_market(indicators)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_overbought_detection(self):
        indicators = {
            "rsi": 80.0,
            "macd": 5.0,
            "signal": 3.0,
            "histogram": 2.0,
            "sma5": 2600.0,
            "sma13": 2550.0,
            "sma25": 2500.0,
            "current_price": 2650.0,
        }
        result = analyze_market(indicators)
        assert "買われすぎ" in result

    def test_oversold_detection(self):
        indicators = {
            "rsi": 20.0,
            "macd": -5.0,
            "signal": -3.0,
            "histogram": -2.0,
            "sma5": 2400.0,
            "sma13": 2450.0,
            "sma25": 2500.0,
            "current_price": 2350.0,
        }
        result = analyze_market(indicators)
        assert "売られすぎ" in result

    def test_golden_cross(self):
        indicators = {
            "rsi": 55.0,
            "macd": 5.0,
            "signal": 3.0,
            "histogram": 2.0,
            "sma5": 2600.0,
            "sma13": 2550.0,
            "sma25": 2500.0,
            "current_price": 2650.0,
        }
        result = analyze_market(indicators)
        assert "ゴールデンクロス" in result

    def test_dead_cross(self):
        indicators = {
            "rsi": 45.0,
            "macd": -5.0,
            "signal": -3.0,
            "histogram": -2.0,
            "sma5": 2400.0,
            "sma13": 2450.0,
            "sma25": 2500.0,
            "current_price": 2350.0,
        }
        result = analyze_market(indicators)
        assert "デッドクロス" in result
