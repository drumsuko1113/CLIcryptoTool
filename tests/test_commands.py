"""コマンドハンドラのテスト（特に /position サブコマンド: Issue #30）"""
import os
import tempfile
import threading
from unittest.mock import MagicMock

from src.commands import CommandHandler
from src.position import PositionManager


def _make_handler(prices=None):
    """テスト用の CommandHandler を組み立てる"""
    market_state = MagicMock()
    market_state.prices = prices or {
        "eth_usd": 2700.0,
        "eth_jpy": 405000.0,
        "high_usd": 2800.0,
        "low_usd": 2600.0,
        "volume": 100000.0,
        "change_percent": 1.0,
        "usd_jpy_rate": 150.0,
    }
    alert_manager = MagicMock()
    alert_manager.alerts = []

    tmpdir = tempfile.mkdtemp()
    config_path = os.path.join(tmpdir, "position.json")
    position_manager = PositionManager(config_path)

    handler = CommandHandler(
        market_state=market_state,
        alert_manager=alert_manager,
        position_manager=position_manager,
        refresh_fn=lambda: None,
        render_fn=lambda: None,
        data_lock=threading.Lock(),
    )
    return handler, position_manager, config_path


class TestPositionAddSubcommand:
    def test_add_basic_usd(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "2500", "1.5"])
        assert len(pm.positions) == 1
        assert pm.positions[0]["entry_price"] == 2500.0
        assert pm.positions[0]["amount"] == 1.5
        assert pm.positions[0]["currency"] == "USD"

    def test_add_with_jpy_currency(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "400000", "0.5", "JPY"])
        assert pm.positions[0]["currency"] == "JPY"
        assert pm.positions[0]["entry_price"] == 400000.0

    def test_add_currency_case_insensitive(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "2500", "1", "usd"])
        assert pm.positions[0]["currency"] == "USD"

    def test_add_persists_to_disk(self):
        handler, pm, config_path = _make_handler()
        handler.cmd_position(["add", "2500", "1.0"])
        # ディスクから別インスタンスで読み直して確認
        reloaded = PositionManager(config_path)
        assert len(reloaded.positions) == 1
        assert reloaded.positions[0]["entry_price"] == 2500.0

    def test_add_rejects_invalid_price(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "abc", "1.0"])
        assert pm.positions == []

    def test_add_rejects_invalid_amount(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "2500", "xyz"])
        assert pm.positions == []

    def test_add_rejects_missing_args(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "2500"])  # amount 不足
        assert pm.positions == []

    def test_add_rejects_unknown_currency(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["add", "2500", "1", "EUR"])
        assert pm.positions == []


class TestPositionRemoveSubcommand:
    def test_remove_existing(self):
        handler, pm, _ = _make_handler()
        pm.add_position(2500.0, 1.0)
        pm.add_position(2600.0, 0.5)
        handler.cmd_position(["remove", "0"])
        assert len(pm.positions) == 1
        assert pm.positions[0]["entry_price"] == 2600.0

    def test_remove_persists_to_disk(self):
        handler, pm, config_path = _make_handler()
        pm.add_position(2500.0, 1.0)
        pm.save()
        handler.cmd_position(["remove", "0"])
        reloaded = PositionManager(config_path)
        assert reloaded.positions == []

    def test_remove_invalid_index(self):
        handler, pm, _ = _make_handler()
        pm.add_position(2500.0, 1.0)
        handler.cmd_position(["remove", "99"])
        assert len(pm.positions) == 1  # 削除されない

    def test_remove_non_numeric_index(self):
        handler, pm, _ = _make_handler()
        pm.add_position(2500.0, 1.0)
        handler.cmd_position(["remove", "foo"])
        assert len(pm.positions) == 1

    def test_remove_missing_index(self):
        handler, pm, _ = _make_handler()
        pm.add_position(2500.0, 1.0)
        handler.cmd_position(["remove"])
        assert len(pm.positions) == 1


class TestPositionClearSubcommand:
    def test_clear_removes_all(self):
        handler, pm, _ = _make_handler()
        pm.add_position(2500.0, 1.0)
        pm.add_position(2600.0, 0.5)
        handler.cmd_position(["clear"])
        assert pm.positions == []

    def test_clear_persists_to_disk(self):
        handler, pm, config_path = _make_handler()
        pm.add_position(2500.0, 1.0)
        pm.save()
        handler.cmd_position(["clear"])
        reloaded = PositionManager(config_path)
        assert reloaded.positions == []

    def test_clear_when_empty(self):
        handler, pm, _ = _make_handler()
        handler.cmd_position(["clear"])
        assert pm.positions == []
