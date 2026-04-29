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


class TestPositionAggregates:
    """Issue #35: 平均取得単価・全体損益の集計"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "position.json")
        self.manager = PositionManager(self.config_path)

    def test_avg_entry_price_single(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        assert self.manager.avg_entry_price("USD") == 2500.0

    def test_avg_entry_price_weighted(self):
        # 2500 × 1.0 + 2700 × 3.0 = 10600 / 4.0 = 2650
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2700.0, 3.0, "USD")
        assert self.manager.avg_entry_price("USD") == 2650.0

    def test_avg_entry_price_no_positions_returns_none(self):
        assert self.manager.avg_entry_price("USD") is None

    def test_avg_entry_price_filters_by_currency(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(400000.0, 1.0, "JPY")
        assert self.manager.avg_entry_price("USD") == 2500.0
        assert self.manager.avg_entry_price("JPY") == 400000.0

    def test_total_amount(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2700.0, 0.5, "USD")
        assert self.manager.total_amount("USD") == 1.5

    def test_total_amount_filters_by_currency(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(400000.0, 2.0, "JPY")
        assert self.manager.total_amount("USD") == 1.0
        assert self.manager.total_amount("JPY") == 2.0

    def test_total_unrealized_pnl_profit(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2600.0, 0.5, "USD")
        # current=2700: (2700-2500)*1 + (2700-2600)*0.5 = 200 + 50 = 250
        result = self.manager.total_unrealized_pnl(2700.0, "USD")
        assert result["pnl"] == 250.0
        # cost: 2500*1 + 2600*0.5 = 3800; pct = 250/3800 * 100
        assert abs(result["pnl_percent"] - (250.0 / 3800.0 * 100)) < 1e-9

    def test_total_unrealized_pnl_loss(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        result = self.manager.total_unrealized_pnl(2300.0, "USD")
        assert result["pnl"] == -200.0
        assert result["pnl_percent"] < 0

    def test_total_unrealized_pnl_no_positions(self):
        result = self.manager.total_unrealized_pnl(2700.0, "USD")
        assert result["pnl"] == 0.0
        assert result["pnl_percent"] == 0.0

    def test_currencies_in_use(self):
        """通貨集合を返すヘルパー（混在対応）"""
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(400000.0, 1.0, "JPY")
        assert set(self.manager.currencies_in_use()) == {"USD", "JPY"}


class TestFormatPositionsSummary:
    """Issue #35: format_positions が集計セクションを追加で出す"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "position.json")
        self.manager = PositionManager(self.config_path)

    def test_no_summary_when_single_position(self):
        """単一ポジションでは集計セクションは出さない（情報過多回避）"""
        self.manager.add_position(2500.0, 1.0, "USD")
        out = self.manager.format_positions(2700.0, 400000.0)
        assert "平均取得" not in out

    def test_summary_when_multiple_positions(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2600.0, 0.5, "USD")
        out = self.manager.format_positions(2700.0, 400000.0)
        assert "平均取得" in out
        # 平均取得 = (2500*1 + 2600*0.5) / 1.5 = 2533.33
        assert "2,533.33" in out

    def test_summary_includes_total_pnl(self):
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2600.0, 0.5, "USD")
        out = self.manager.format_positions(2700.0, 400000.0)
        # 全体損益 = 200 + 50 = 250
        assert "250.00" in out

    def test_summary_per_currency_when_mixed(self):
        """USD/JPY 混在時は通貨ごとに集計（>= 2 件のみ）"""
        self.manager.add_position(2500.0, 1.0, "USD")
        self.manager.add_position(2700.0, 1.0, "USD")
        self.manager.add_position(400000.0, 1.0, "JPY")
        self.manager.add_position(420000.0, 1.0, "JPY")
        out = self.manager.format_positions(2800.0, 430000.0)
        # 両通貨の集計が出ている
        assert "USD" in out and "JPY" in out
        # USD 平均: 2600
        assert "2,600.00" in out
        # JPY 平均: 410000
        assert "410,000" in out
