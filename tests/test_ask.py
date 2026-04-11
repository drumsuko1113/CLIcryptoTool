"""claude.ai連携モジュールのテスト"""
from unittest.mock import patch
from src.ask import generate_prompt


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


class TestCopyAndOpen:
    def test_copy_to_clipboard_calls_powershell(self):
        """copy_to_clipboardがsubprocess.runを呼ぶこと"""
        with patch("src.ask.subprocess.run") as mock_run:
            from src.ask import copy_to_clipboard
            copy_to_clipboard("テスト日本語テキスト")
            mock_run.assert_called_once()
            # PowerShellコマンドにSet-Clipboardが含まれること
            call_args = mock_run.call_args[0][0]
            assert "powershell" in call_args[0].lower()

    def test_copy_to_clipboard_uses_set_clipboard(self):
        """PowerShellのSet-Clipboardが呼ばれること"""
        with patch("src.ask.subprocess.run") as mock_run:
            from src.ask import copy_to_clipboard
            copy_to_clipboard("日本語テスト")
            call_args = mock_run.call_args[0][0]
            cmd_str = " ".join(call_args)
            assert "Set-Clipboard" in cmd_str

    def test_open_claude_ai(self):
        with patch("src.ask.webbrowser.open") as mock_open:
            from src.ask import open_claude_ai
            open_claude_ai()
            mock_open.assert_called_once()
