"""ポジション管理モジュールのテスト"""
import os
import tempfile
from src.position import PositionManager


class TestPositionManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "position.json")
        self.manager = PositionManager(self.config_path)

    def test_add_position(self):
        self.manager.add_position(2500.0, 1.5, "USD")
        assert len(self.manager.positions) == 1
        assert self.manager.positions[0]["entry_price"] == 2500.0
        assert self.manager.positions[0]["amount"] == 1.5

    def test_save_and_load(self):
        self.manager.add_position(2500.0, 1.5, "USD")
        self.manager.save()

        manager2 = PositionManager(self.config_path)
        manager2.load()
        assert len(manager2.positions) == 1
        assert manager2.positions[0]["entry_price"] == 2500.0

    def test_calc_pnl_profit(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        pnl = self.manager.calc_pnl(0, 2700.0)
        assert pnl["pnl"] == 200.0
        assert pnl["pnl_percent"] > 0

    def test_calc_pnl_loss(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        pnl = self.manager.calc_pnl(0, 2300.0)
        assert pnl["pnl"] == -200.0
        assert pnl["pnl_percent"] < 0

    def test_record_trade(self):
        self.manager.record_trade(200.0, "USD")
        assert self.manager.trade_history[0]["profit"] == 200.0
        assert self.manager.total_profit == 200.0

    def test_cumulative_profit(self):
        self.manager.record_trade(200.0, "USD")
        self.manager.record_trade(-50.0, "USD")
        assert self.manager.total_profit == 150.0

    def test_format_position_display(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        output = self.manager.format_positions(2700.0, 400000.0)
        assert "2,500.00" in output
        assert "$" in output

    def test_format_empty_positions(self):
        output = self.manager.format_positions(2700.0, 400000.0)
        assert "なし" in output or "ポジション" in output

    def test_remove_position(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2600.0, 0.5, "USD")
        self.manager.remove_position(0)
        assert len(self.manager.positions) == 1
        assert self.manager.positions[0]["entry_price"] == 2600.0

    def test_clear_positions(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2600.0, 0.5, "USD")
        self.manager.clear_positions()
        assert self.manager.positions == []

    def test_clear_positions_when_empty(self):
        self.manager.clear_positions()
        assert self.manager.positions == []

    def test_clear_positions_does_not_touch_history(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.record_trade(100.0, "USD")
        self.manager.clear_positions()
        assert self.manager.trade_history[0]["profit"] == 100.0
        assert self.manager.total_profit == 100.0
