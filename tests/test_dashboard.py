"""ダッシュボードUIモジュールのテスト"""
from unittest.mock import MagicMock
from rich.console import Console
from src.dashboard import (
    build_header,
    build_price_panel,
    build_chart_panel,
    build_indicators_panel,
    build_position_panel,
    build_dashboard,
    MarketState,
)
from src.theme import STYLE_UP, STYLE_DOWN


def _sample_market_state():
    """テスト用のMarketState"""
    state = MarketState()
    state.prices = {
        "eth_usd": 2500.0,
        "eth_jpy": 387500.0,
        "high_usd": 2600.0,
        "low_usd": 2400.0,
        "high_jpy": 403000.0,
        "low_jpy": 372000.0,
        "volume": 150000.0,
        "change_percent": 2.35,
        "usd_jpy_rate": 155.0,
    }
    state.closes = [float(2500 + i * 5) for i in range(50)]
    state.klines = [
        [0, str(2500 + i * 5), str(2520 + i * 5),
         str(2490 + i * 5), str(2505 + i * 5), "100",
         0, "0", "0", "0", "0", "0"]
        for i in range(50)
    ]
    return state


class TestStyles:
    def test_up_style_exists(self):
        assert STYLE_UP is not None

    def test_down_style_exists(self):
        assert STYLE_DOWN is not None


class TestBuildHeader:
    def test_returns_renderable(self):
        result = build_header()
        console = Console(file=MagicMock(), width=80)
        # renderableであればエラーなく render できる
        console.print(result)


class TestBuildPricePanel:
    def test_returns_renderable(self):
        state = _sample_market_state()
        result = build_price_panel(state)
        console = Console(file=MagicMock(), width=80)
        console.print(result)

    def test_returns_renderable_no_data(self):
        state = MarketState()
        result = build_price_panel(state)
        console = Console(file=MagicMock(), width=80)
        console.print(result)


class TestBuildChartPanel:
    def test_returns_renderable(self):
        state = _sample_market_state()
        result = build_chart_panel(state, width=60)
        console = Console(file=MagicMock(), width=80)
        console.print(result)

    def test_returns_renderable_no_data(self):
        state = MarketState()
        result = build_chart_panel(state, width=60)
        console = Console(file=MagicMock(), width=80)
        console.print(result)


class TestBuildIndicatorsPanel:
    def test_returns_renderable(self):
        state = _sample_market_state()
        result = build_indicators_panel(state)
        console = Console(file=MagicMock(), width=80)
        console.print(result)


class TestBuildPositionPanel:
    def test_returns_renderable(self):
        state = _sample_market_state()
        result = build_position_panel(state)
        console = Console(file=MagicMock(), width=80)
        console.print(result)


class TestBuildDashboard:
    def test_returns_renderable(self):
        state = _sample_market_state()
        result = build_dashboard(state, width=100)
        console = Console(file=MagicMock(), width=100)
        console.print(result)

    def test_returns_renderable_empty_state(self):
        state = MarketState()
        result = build_dashboard(state, width=100)
        console = Console(file=MagicMock(), width=100)
        console.print(result)


class TestMarketState:
    def test_initial_state(self):
        state = MarketState()
        assert state.prices is None
        assert state.closes == []
        assert state.klines == []

    def test_has_data_false(self):
        state = MarketState()
        assert state.has_data is False

    def test_has_data_true(self):
        state = _sample_market_state()
        assert state.has_data is True
