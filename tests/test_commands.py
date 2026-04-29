"""コマンドハンドラのテスト（特に /position サブコマンド: Issue #30）"""
import os
import tempfile
import threading
from unittest.mock import MagicMock

from src.commands import CommandHandler
from src.dashboard import MarketState
from src.position import PositionManager


def _make_handler(prices=None, refresh_fn=None, render_fn=None,
                  with_long=False):
    """テスト用の CommandHandler を組み立てる"""
    market_state = MarketState()
    market_state.prices = prices or {
        "eth_usd": 2700.0,
        "eth_jpy": 405000.0,
        "high_usd": 2800.0,
        "low_usd": 2600.0,
        "volume": 100000.0,
        "change_percent": 1.0,
        "usd_jpy_rate": 150.0,
    }
    market_state.closes = [float(2500 + i * 5) for i in range(50)]
    market_state.klines = [
        [0, str(2500 + i * 5), str(2520 + i * 5),
         str(2490 + i * 5), str(2505 + i * 5), "100",
         0, "0", "0", "0", "0", "0"]
        for i in range(50)
    ]
    alert_manager = MagicMock()
    alert_manager.alerts = []

    tmpdir = tempfile.mkdtemp()
    config_path = os.path.join(tmpdir, "position.json")
    position_manager = PositionManager(config_path)
    long_position_manager = None
    long_config_path = None
    if with_long:
        long_config_path = os.path.join(tmpdir, "long_position.json")
        long_position_manager = PositionManager(long_config_path)

    handler = CommandHandler(
        market_state=market_state,
        alert_manager=alert_manager,
        position_manager=position_manager,
        refresh_fn=refresh_fn or (lambda: None),
        render_fn=render_fn or (lambda: None),
        data_lock=threading.Lock(),
        long_position_manager=long_position_manager,
    )
    if with_long:
        return handler, position_manager, long_position_manager, long_config_path
    return handler, position_manager, config_path


class TestPerCommandPanel:
    """Issue #34: 各コマンドは対応するパネルだけを表示する"""

    def test_price_does_not_render_full_dashboard(self):
        """/price は全体描画関数（render_fn）を呼ばない"""
        render = MagicMock()
        refresh = MagicMock()
        handler, _, _ = _make_handler(refresh_fn=refresh, render_fn=render)
        handler.cmd_price([])
        render.assert_not_called()

    def test_price_refreshes_data(self):
        """/price は最新データのために refresh は呼ぶ"""
        refresh = MagicMock()
        render = MagicMock()
        handler, _, _ = _make_handler(refresh_fn=refresh, render_fn=render)
        handler.cmd_price([])
        refresh.assert_called_once()

    def test_chart_does_not_render_full_dashboard(self):
        """/chart は全体描画関数を呼ばない"""
        render = MagicMock()
        refresh = MagicMock()
        handler, _, _ = _make_handler(refresh_fn=refresh, render_fn=render)
        handler.cmd_chart([])
        render.assert_not_called()

    def test_chart_refreshes_data(self):
        refresh = MagicMock()
        render = MagicMock()
        handler, _, _ = _make_handler(refresh_fn=refresh, render_fn=render)
        handler.cmd_chart([])
        refresh.assert_called_once()

    def test_refresh_still_renders_full_dashboard(self):
        """/refresh は引き続き全体描画する"""
        render = MagicMock()
        refresh = MagicMock()
        handler, _, _ = _make_handler(refresh_fn=refresh, render_fn=render)
        handler.cmd_refresh([])
        refresh.assert_called_once()
        render.assert_called_once()


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


class TestLongPositionCommand:
    """Issue #37: /longposition の追加・削除・全削除・表示"""

    def test_add_long_position(self):
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        handler.cmd_longposition(["add", "1800", "2.0"])
        assert len(long_pm.positions) == 1
        assert long_pm.positions[0]["entry_price"] == 1800.0
        # スイング側には増えていない
        assert swing.positions == []

    def test_long_position_persists_independently(self):
        handler, swing, long_pm, long_path = _make_handler(with_long=True)
        handler.cmd_longposition(["add", "1800", "2.0"])
        reloaded = PositionManager(long_path)
        assert len(reloaded.positions) == 1

    def test_remove_long_position(self):
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        long_pm.add_position(1800.0, 2.0)
        long_pm.add_position(1900.0, 1.0)
        handler.cmd_longposition(["remove", "0"])
        assert len(long_pm.positions) == 1
        assert long_pm.positions[0]["entry_price"] == 1900.0

    def test_clear_long_positions(self):
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        long_pm.add_position(1800.0, 2.0)
        long_pm.add_position(1900.0, 1.0)
        handler.cmd_longposition(["clear"])
        assert long_pm.positions == []

    def test_long_position_does_not_affect_swing(self):
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        swing.add_position(2500.0, 1.0)
        handler.cmd_longposition(["add", "1800", "2.0"])
        handler.cmd_longposition(["clear"])
        # スイングは無傷
        assert len(swing.positions) == 1


class TestPositionDisplayWithLong:
    """Issue #37: /position 実行時にスイング分と長期分を分けて表示"""

    def test_position_displays_long_section_when_long_exists(self):
        """長期ポジションがあれば /position の出力に長期セクションが含まれる"""
        from rich.console import Console as _Console
        import io
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        swing.add_position(2500.0, 1.0)
        long_pm.add_position(1800.0, 2.0)

        # console.print の出力を捕捉
        buf = io.StringIO()
        from src import commands as _cmds
        old_console = _cmds.console
        _cmds.console = _Console(
            file=buf, width=120, force_terminal=False, legacy_windows=False
        )
        try:
            handler.cmd_position([])
        finally:
            _cmds.console = old_console

        output = buf.getvalue()
        assert "スイングポジション" in output
        assert "長期保有ポジション" in output

    def test_position_no_long_section_when_long_empty(self):
        """長期ポジションが空なら長期セクションは出ない（情報過多回避）"""
        from rich.console import Console as _Console
        import io
        handler, swing, long_pm, _ = _make_handler(with_long=True)
        swing.add_position(2500.0, 1.0)

        buf = io.StringIO()
        from src import commands as _cmds
        old_console = _cmds.console
        _cmds.console = _Console(
            file=buf, width=120, force_terminal=False, legacy_windows=False
        )
        try:
            handler.cmd_position([])
        finally:
            _cmds.console = old_console

        output = buf.getvalue()
        assert "長期保有ポジション" not in output


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
