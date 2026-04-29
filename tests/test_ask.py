"""claude.ai連携モジュールのテスト"""
from unittest.mock import patch
from src.ask import generate_prompt, open_claude_ai


class TestGeneratePrompt:
    def test_returns_string(self):
        market_data = {
            "eth_usd": 2500.0,
            "eth_jpy": 387500.0,
            "change_percent": 2.5,
            "rsi": 65.0,
            "macd": 3.5,
            "signal": 2.1,
            "sma5": 2520.0,
            "sma13": 2480.0,
            "sma25": 2450.0,
        }
        result = generate_prompt(market_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_price_info(self):
        market_data = {
            "eth_usd": 2500.0,
            "eth_jpy": 387500.0,
            "change_percent": 2.5,
            "rsi": 65.0,
            "macd": 3.5,
            "signal": 2.1,
            "sma5": 2520.0,
            "sma13": 2480.0,
            "sma25": 2450.0,
        }
        result = generate_prompt(market_data)
        assert "2500" in result or "2,500" in result
        assert "RSI" in result
        assert "MACD" in result
        assert "SMA" in result

    def test_contains_japanese(self):
        market_data = {
            "eth_usd": 2500.0,
            "eth_jpy": 387500.0,
            "change_percent": 2.5,
            "rsi": 65.0,
            "macd": 3.5,
            "signal": 2.1,
            "sma5": 2520.0,
            "sma13": 2480.0,
            "sma25": 2450.0,
        }
        result = generate_prompt(market_data)
        assert "ETH" in result


class TestGeneratePromptWithPositions:
    """Issue #36: 現在のポジション状況をプロンプトに含める"""

    def _market_data(self):
        return {
            "eth_usd": 2700.0,
            "eth_jpy": 405000.0,
            "change_percent": 1.0,
            "rsi": 55.0,
            "macd": 2.0,
            "signal": 1.5,
            "sma5": 2680.0,
            "sma13": 2650.0,
            "sma25": 2600.0,
        }

    def test_positions_section_appears(self):
        positions = [
            {"entry_price": 2500.0, "amount": 1.0, "currency": "USD"},
        ]
        result = generate_prompt(
            self._market_data(),
            positions=positions,
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        assert "保有ポジション" in result or "ポジション" in result
        assert "2,500" in result or "2500" in result

    def test_pnl_calculated_in_prompt(self):
        """プロンプトに含み損益（金額・%）が出ている"""
        positions = [
            {"entry_price": 2500.0, "amount": 1.0, "currency": "USD"},
        ]
        result = generate_prompt(
            self._market_data(),
            positions=positions,
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        # +$200, +8.00%
        assert "200" in result
        assert "8.00" in result

    def test_aggregate_summary_with_multiple(self):
        """複数ポジションがあれば集計サマリーが出る"""
        positions = [
            {"entry_price": 2500.0, "amount": 1.0, "currency": "USD"},
            {"entry_price": 2600.0, "amount": 0.5, "currency": "USD"},
        ]
        result = generate_prompt(
            self._market_data(),
            positions=positions,
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        # 平均取得 2533.33
        assert "2,533.33" in result or "2533.33" in result
        # 合計含み損益 +$250
        assert "250.00" in result

    def test_no_positions_message(self):
        """ポジションが空の場合は「現在ポジションなし」を明記"""
        result = generate_prompt(
            self._market_data(),
            positions=[],
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        assert "ポジションなし" in result or "ポジション: なし" in result

    def test_realized_profit_included(self):
        """スイング累計実現益が渡された場合プロンプトに含まれる"""
        result = generate_prompt(
            self._market_data(),
            positions=[],
            current_prices={"USD": 2700.0, "JPY": 405000.0},
            realized_profit=1234.56,
        )
        assert "1,234.56" in result or "1234.56" in result

    def test_long_positions_separate_section(self):
        """Issue #37: 長期保有ポジションはスイング分と別セクションで出る"""
        positions = [
            {"entry_price": 2500.0, "amount": 1.0, "currency": "USD"},
        ]
        long_positions = [
            {"entry_price": 1800.0, "amount": 2.0, "currency": "USD"},
        ]
        result = generate_prompt(
            self._market_data(),
            positions=positions,
            long_positions=long_positions,
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        # 両セクションのラベルが存在
        assert "スイング" in result
        assert "長期保有" in result or "長期" in result
        # 両ポジションの仕入値が含まれる
        assert "2,500" in result or "2500" in result
        assert "1,800" in result or "1800" in result

    def test_long_positions_only_when_swing_empty(self):
        """スイングなし・長期のみでも長期セクションが出る"""
        long_positions = [
            {"entry_price": 1800.0, "amount": 2.0, "currency": "USD"},
        ]
        result = generate_prompt(
            self._market_data(),
            positions=[],
            long_positions=long_positions,
            current_prices={"USD": 2700.0, "JPY": 405000.0},
        )
        assert "1,800" in result or "1800" in result

    def test_backwards_compat_no_kwargs(self):
        """既存の呼び出し（market_data のみ）でも動く"""
        result = generate_prompt(self._market_data())
        assert isinstance(result, str)
        assert "RSI" in result


class TestPlatformUtils:
    def test_copy_to_clipboard_calls_powershell(self):
        with patch("src.platform_utils.subprocess.run") as mock_run:
            from src.platform_utils import copy_to_clipboard
            copy_to_clipboard("テスト日本語テキスト")
            mock_run.assert_called_once()

    def test_open_claude_ai(self):
        with patch("src.platform_utils.webbrowser.open") as mock_open:
            open_claude_ai()
            mock_open.assert_called_once()
