"""メインREPLモジュールのテスト"""
from src.main import parse_command, COMMANDS


class TestParseCommand:
    def test_price_command(self):
        cmd, args = parse_command("/price")
        assert cmd == "price"
        assert args == []

    def test_alert_with_args(self):
        cmd, args = parse_command("/alert 350000")
        assert cmd == "alert"
        assert args == ["350000"]

    def test_unknown_command(self):
        cmd, args = parse_command("/unknown")
        assert cmd == "unknown"

    def test_empty_input(self):
        cmd, args = parse_command("")
        assert cmd is None

    def test_non_command_input(self):
        cmd, args = parse_command("hello")
        assert cmd is None

    def test_help_command(self):
        cmd, args = parse_command("/help")
        assert cmd == "help"

    def test_quit_command(self):
        cmd, args = parse_command("/quit")
        assert cmd == "quit"

    def test_alert_remove(self):
        cmd, args = parse_command("/alert remove 0")
        assert cmd == "alert"
        assert args == ["remove", "0"]

    def test_alert_clear(self):
        cmd, args = parse_command("/alert clear")
        assert cmd == "alert"
        assert args == ["clear"]


class TestCommands:
    def test_commands_dict_has_required_keys(self):
        required = [
            "price", "chart", "news", "iran",
            "analysis", "position", "alert", "ask",
            "help", "quit",
        ]
        for key in required:
            assert key in COMMANDS, f"Missing command: {key}"
