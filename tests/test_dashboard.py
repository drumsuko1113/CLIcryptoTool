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
    _build_chart_text,
)
from src.theme import STYLE_UP, STYLE_DOWN, CHART_UP, CHART_DOWN, COLOR_UP, COLOR_DOWN


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


class TestChartTextAxis:
    """チャート縦軸のラベル描画（USD 左・JPY 右）をテストする"""

    def _sample_args(self):
        state = _sample_market_state()
        return state.klines, state.closes

    def test_usd_axis_always_rendered(self):
        klines, closes = self._sample_args()
        text = _build_chart_text(klines, closes, width=40, height=8).plain
        assert "$" in text

    def test_jpy_axis_appears_when_rate_given(self):
        klines, closes = self._sample_args()
        text = _build_chart_text(
            klines, closes, width=40, height=8, usd_jpy_rate=155.0
        ).plain
        assert "¥" in text

    def test_jpy_axis_absent_without_rate(self):
        klines, closes = self._sample_args()
        text = _build_chart_text(klines, closes, width=40, height=8).plain
        assert "¥" not in text

    def test_jpy_value_matches_usd_times_rate(self):
        """JPY ラベルは USD × レートを四捨五入した値になっている"""
        klines, closes = self._sample_args()
        rate = 150.0
        text = _build_chart_text(
            klines, closes, width=40, height=8, usd_jpy_rate=rate
        ).plain
        # 最高値行の USD / JPY を抽出（右寄せの先行スペースを skip）
        first_line = text.split("\n")[0]
        usd_part = first_line.split("$", 1)[1].strip().split()[0].replace(",", "")
        jpy_part = first_line.rsplit("¥", 1)[1].strip().split()[0].replace(",", "")
        assert int(jpy_part) == round(float(usd_part) * rate)

    def test_build_chart_panel_uses_rate_from_state(self):
        """state.prices にレートがあれば build_chart_panel が JPY 軸を描く"""
        import io
        state = _sample_market_state()
        buf = io.StringIO()
        console = Console(
            file=buf, width=120, force_terminal=False, legacy_windows=False
        )
        console.print(build_chart_panel(state, width=80))
        assert "¥" in buf.getvalue()

    def test_build_chart_panel_no_rate_no_jpy(self):
        """state.prices が None の場合は JPY 軸なし"""
        import io
        state = MarketState()
        # klines だけセットして prices は None のまま
        state.klines = _sample_market_state().klines
        state.closes = _sample_market_state().closes
        buf = io.StringIO()
        console = Console(
            file=buf, width=120, force_terminal=False, legacy_windows=False
        )
        console.print(build_chart_panel(state, width=80))
        assert "¥" not in buf.getvalue()


class TestChartCandleColors:
    """ローソク足の色がチャート専用色定数（CHART_UP/CHART_DOWN）を使う"""

    def test_chart_colors_differ_from_global(self):
        """チャート色は PNL 等の COLOR_UP/COLOR_DOWN と独立している"""
        assert CHART_UP != COLOR_UP
        assert CHART_DOWN != COLOR_DOWN

    def test_chart_up_is_red(self):
        """上昇足は赤系（Issue #31: 日本式の慣習に合わせる）"""
        assert CHART_UP.lower() == "#ff5252"

    def test_chart_down_is_blue(self):
        """下落足は青系（Issue #31）"""
        assert CHART_DOWN.lower() == "#4fc3f7"

    def test_chart_text_uses_chart_colors_for_candles(self):
        """ローソク足の実体描画に CHART_UP/CHART_DOWN が使われている"""
        # 上昇足だけのデータ
        up_klines = [
            [0, "2500", "2520", "2495", "2515", "100",
             0, "0", "0", "0", "0", "0"]
            for _ in range(20)
        ]
        up_closes = [2515.0] * 20
        text = _build_chart_text(up_klines, up_closes, width=20, height=8)
        styles = {str(span.style) for span in text.spans}
        assert any(CHART_UP in s for s in styles)
        assert not any(f"bold {COLOR_UP}" == s for s in styles)

        # 下落足だけのデータ
        down_klines = [
            [0, "2500", "2520", "2480", "2485", "100",
             0, "0", "0", "0", "0", "0"]
            for _ in range(20)
        ]
        down_closes = [2485.0] * 20
        text = _build_chart_text(down_klines, down_closes, width=20, height=8)
        styles = {str(span.style) for span in text.spans}
        assert any(CHART_DOWN in s for s in styles)


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
