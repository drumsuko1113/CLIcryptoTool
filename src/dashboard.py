"""ダッシュボードUI モジュール - Bloomberg風プロトレーダー端末"""
from datetime import datetime

from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich import box

from src.chart import calc_sma
from src.theme import (
    COLOR_BG_HEADER, COLOR_BORDER, COLOR_BORDER_DIM,
    COLOR_UP, COLOR_DOWN, COLOR_LABEL, COLOR_VALUE,
    COLOR_ACCENT, COLOR_MUTED, COLOR_TITLE, COLOR_WARN,
    STYLE_UP, STYLE_DOWN, STYLE_LABEL, STYLE_VALUE,
    CHAR_BODY_UP, CHAR_BODY_DOWN, CHAR_WICK, CHAR_BAR_FILL, CHAR_BAR_EMPTY,
)


class MarketState:
    """ダッシュボードに表示する市場データをまとめるクラス"""

    def __init__(self):
        self.prices = None
        self.closes = []
        self.klines = []
        self.position_manager = None
        self.alert_manager = None
        self.last_update = None
        # 計算済みテクニカル指標
        self.rsi = None
        self.macd = None
        self.signal = None
        self.histogram = None
        self.sma5 = []
        self.sma13 = []
        self.sma25 = []

    @property
    def has_data(self):
        return self.prices is not None and len(self.closes) > 0

    def compute_indicators(self):
        """テクニカル指標を一括計算してキャッシュする"""
        from src.chart import calc_rsi, calc_macd
        if len(self.closes) < 5:
            return
        self.sma5 = calc_sma(self.closes, 5)
        self.sma13 = calc_sma(self.closes, 13)
        self.sma25 = calc_sma(self.closes, 25)
        rsi_vals = calc_rsi(self.closes, 14)
        self.rsi = rsi_vals[-1] if rsi_vals[-1] is not None else None
        macd_line, signal, histogram = calc_macd(self.closes)
        self.macd = macd_line[-1]
        self.signal = signal[-1]
        self.histogram = histogram[-1]


def _arrow(change):
    """変動率に応じた矢印を返す"""
    if change > 0:
        return Text(f"▲ +{change:.2f}%", style=STYLE_UP)
    elif change < 0:
        return Text(f"▼ {change:.2f}%", style=STYLE_DOWN)
    else:
        return Text(f"─ {change:.2f}%", style=STYLE_LABEL)


def _gauge(value, min_val=0, max_val=100, width=20, label=""):
    """ゲージバーを生成する"""
    ratio = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    filled = int(ratio * width)
    empty = width - filled

    if value >= 70:
        color = COLOR_DOWN
    elif value <= 30:
        color = COLOR_UP
    else:
        color = COLOR_ACCENT

    bar = Text()
    if label:
        bar.append(f"{label} ", style=STYLE_LABEL)
    bar.append(CHAR_BAR_FILL * filled, style=f"bold {color}")
    bar.append(CHAR_BAR_EMPTY * empty, style=COLOR_MUTED)
    bar.append(f" {value:.1f}", style=f"bold {color}")
    return bar


def build_header():
    """ヘッダーバーを構築する"""
    now = datetime.now().strftime("%H:%M:%S")
    title = Text()
    title.append("  ◆ ETH TRADING TERMINAL", style=f"bold {COLOR_TITLE}")
    title.append("  v2.0", style=COLOR_MUTED)

    right = Text(f"更新: {now}  ", style=COLOR_LABEL, justify="right")

    table = Table(
        show_header=False, show_edge=False, show_lines=False,
        box=None, padding=0, expand=True,
    )
    table.add_column(ratio=3)
    table.add_column(ratio=1, justify="right")
    table.add_row(title, right)

    return Panel(
        table,
        style=f"on {COLOR_BG_HEADER}",
        border_style=COLOR_BORDER,
        box=box.HEAVY,
        padding=(0, 0),
    )


def build_price_panel(state):
    """価格パネルを構築する（3カラム: ETH/JPY, ETH/USD, Volume）"""
    if not state.has_data:
        return Panel(
            Text("  データ取得中...", style=COLOR_MUTED),
            title="[bold]価格[/]",
            border_style=COLOR_BORDER_DIM,
            box=box.ROUNDED,
        )

    p = state.prices
    change = p["change_percent"]

    # ETH/JPY カラム
    jpy_col = Text()
    jpy_col.append("ETH/JPY\n", style=STYLE_LABEL)
    jpy_col.append(f"¥{p['eth_jpy']:,.0f}\n", style=f"bold {COLOR_VALUE}")
    jpy_col.append_text(_arrow(change))

    # ETH/USD カラム
    usd_col = Text()
    usd_col.append("ETH/USD\n", style=STYLE_LABEL)
    usd_col.append(f"${p['eth_usd']:,.2f}\n", style=f"bold {COLOR_VALUE}")
    usd_col.append(f"H ${p['high_usd']:,.2f}\n", style=COLOR_MUTED)
    usd_col.append(f"L ${p['low_usd']:,.2f}", style=COLOR_MUTED)

    # Volume カラム
    vol_col = Text()
    vol_col.append("24H Volume\n", style=STYLE_LABEL)
    vol_col.append(f"{p['volume']:,.0f} ETH\n", style=f"bold {COLOR_VALUE}")
    vol_col.append(f"USD/JPY: ¥{p['usd_jpy_rate']:.2f}", style=COLOR_MUTED)

    table = Table(
        show_header=False, show_edge=False, show_lines=False,
        box=None, padding=(0, 2), expand=True,
    )
    table.add_column(ratio=1)
    table.add_column(ratio=1)
    table.add_column(ratio=1)
    table.add_row(jpy_col, usd_col, vol_col)

    return Panel(
        table,
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def _build_chart_text(klines, closes, width=60, height=16, usd_jpy_rate=None):
    """ローソク足チャートをrich Textオブジェクトとして構築する

    usd_jpy_rate が指定された場合は右側に円建て価格軸を併記する。
    """
    if not klines:
        return Text("  チャートデータなし", style=COLOR_MUTED)

    display_count = min(len(klines), width)
    display_klines = klines[-display_count:]
    display_closes = closes[-display_count:] if len(closes) >= display_count else closes

    opens = [float(k[1]) for k in display_klines]
    highs = [float(k[2]) for k in display_klines]
    lows = [float(k[3]) for k in display_klines]
    cls = [float(k[4]) for k in display_klines]

    price_min = min(lows)
    price_max = max(highs)
    price_range = price_max - price_min
    if price_range == 0:
        price_range = 1.0

    # SMAを計算
    sma5 = calc_sma(display_closes, 5) if len(display_closes) >= 5 else []
    sma13 = calc_sma(display_closes, 13) if len(display_closes) >= 13 else []
    sma25 = calc_sma(display_closes, 25) if len(display_closes) >= 25 else []

    def price_to_row(price):
        return height - 1 - int((price - price_min) / price_range * (height - 1))

    # グリッド構築: 各セルは (char, style)
    grid = [[(" ", COLOR_MUTED) for _ in range(display_count)] for _ in range(height)]

    # SMAライン描画
    for sma_data, color in [(sma25, "#ffab40"), (sma13, "#ab47bc"), (sma5, "#66bb6a")]:
        if not sma_data:
            continue
        for col in range(len(sma_data)):
            if col < len(sma_data) and sma_data[col] is not None:
                row = price_to_row(sma_data[col])
                if 0 <= row < height:
                    grid[row][col] = ("·", f"bold {color}")

    # ローソク足描画（SMAの上に重ねる）
    for col, (o, h, low, c) in enumerate(zip(opens, highs, lows, cls)):
        h_row = price_to_row(h)
        l_row = price_to_row(low)
        o_row = price_to_row(o)
        c_row = price_to_row(c)
        is_up = c >= o
        body_color = COLOR_UP if is_up else COLOR_DOWN

        # ヒゲ
        for row in range(h_row, l_row + 1):
            if 0 <= row < height:
                grid[row][col] = (CHAR_WICK, COLOR_MUTED)

        # 実体
        body_top = min(o_row, c_row)
        body_bot = max(o_row, c_row)
        char = CHAR_BODY_UP if is_up else CHAR_BODY_DOWN
        for row in range(body_top, body_bot + 1):
            if 0 <= row < height:
                grid[row][col] = (char, body_color)

    # テキスト組み立て
    result = Text()
    for row in range(height):
        price_at_row = price_max - (row / max(1, height - 1)) * price_range
        label = f"${price_at_row:>7,.0f} "
        result.append(label, style=COLOR_MUTED)
        for col in range(display_count):
            char, style = grid[row][col]
            result.append(char, style=style)
        if usd_jpy_rate:
            jpy_at_row = price_at_row * usd_jpy_rate
            result.append(f" ¥{jpy_at_row:>9,.0f}", style=COLOR_MUTED)
        result.append("\n")

    # SMA凡例
    result.append("  ", style=COLOR_MUTED)
    result.append("── SMA5 ", style="bold #66bb6a")
    result.append("── SMA13 ", style="bold #ab47bc")
    result.append("── SMA25", style="bold #ffab40")

    return result


def build_chart_panel(state, width=60):
    """チャートパネルを構築する"""
    jpy_rate = state.prices.get("usd_jpy_rate") if state.prices else None
    jpy_label_width = 11 if jpy_rate else 0
    chart_text = _build_chart_text(
        state.klines, state.closes,
        width=max(20, width - 16 - jpy_label_width), height=14,
        usd_jpy_rate=jpy_rate,
    )
    return Panel(
        chart_text,
        title=f"[bold {COLOR_TITLE}]ETH/USDT 1H[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def build_indicators_panel(state):
    """テクニカル指標パネルを構築する"""
    if not state.has_data or len(state.closes) < 14:
        return Panel(
            Text("  データ不足", style=COLOR_MUTED),
            title=f"[bold {COLOR_TITLE}]指標[/]",
            border_style=COLOR_BORDER_DIM,
            box=box.ROUNDED,
        )

    rsi = state.rsi if state.rsi is not None else 50.0
    macd_v = state.macd if state.macd is not None else 0.0
    sig_v = state.signal if state.signal is not None else 0.0
    hist_v = state.histogram if state.histogram is not None else 0.0
    sma5 = state.sma5
    sma13 = state.sma13
    sma25 = state.sma25

    content = Text()

    # RSI
    content.append("RSI(14)\n", style=f"bold {COLOR_ACCENT}")
    content.append_text(_gauge(rsi, 0, 100, width=22, label=""))
    if rsi >= 70:
        content.append(" 買われすぎ", style=COLOR_DOWN)
    elif rsi <= 30:
        content.append(" 売られすぎ", style=COLOR_UP)
    content.append("\n\n")

    # MACD
    content.append("MACD\n", style=f"bold {COLOR_ACCENT}")
    macd_style = STYLE_UP if macd_v > sig_v else STYLE_DOWN
    cross = "▲ GC" if macd_v > sig_v else "▼ DC"
    content.append(f"  MACD: {macd_v:>8.2f}  ", style=STYLE_VALUE)
    content.append(f"{cross}\n", style=macd_style)
    content.append(f"  Signal: {sig_v:>6.2f}\n", style=COLOR_MUTED)
    content.append(f"  Hist: {hist_v:>8.2f}\n\n", style=macd_style)

    # SMA
    content.append("移動平均\n", style=f"bold {COLOR_ACCENT}")
    for period, data, color in [
        (5, sma5, "#66bb6a"), (13, sma13, "#ab47bc"), (25, sma25, "#ffab40")
    ]:
        val = data[-1] if data and data[-1] is not None else None
        if val:
            content.append(f"  SMA{period:>2}: ", style=COLOR_LABEL)
            content.append(f"${val:>8,.2f}\n", style=f"bold {color}")

    return Panel(
        content,
        title=f"[bold {COLOR_TITLE}]テクニカル指標[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def build_position_panel(state):
    """ポジション・アラートパネルを構築する"""
    content = Text()

    # ポジション
    content.append("ポジション\n", style=f"bold {COLOR_ACCENT}")
    if state.position_manager and state.position_manager.positions and state.prices:
        for i, pos in enumerate(state.position_manager.positions):
            entry = pos["entry_price"]
            amount = pos["amount"]
            currency = pos["currency"]
            current = state.prices["eth_usd"] if currency == "USD" else state.prices["eth_jpy"]
            pnl = (current - entry) * amount
            pnl_pct = ((current - entry) / entry) * 100
            sym = "$" if currency == "USD" else "¥"
            style = STYLE_UP if pnl >= 0 else STYLE_DOWN
            sign = "+" if pnl >= 0 else ""
            content.append(f"  {sym}{entry:,.0f} x{amount} ", style=COLOR_LABEL)
            content.append(f"{sign}{sym}{pnl:,.0f}", style=style)
            content.append(f" ({sign}{pnl_pct:.1f}%)\n", style=style)

        tp = state.position_manager.total_profit
        tp_style = STYLE_UP if tp >= 0 else STYLE_DOWN
        content.append("  累計: ", style=COLOR_LABEL)
        content.append(f"${tp:,.2f}\n", style=tp_style)
    else:
        content.append("  なし\n", style=COLOR_MUTED)

    # アラート
    content.append("\nアラート\n", style=f"bold {COLOR_ACCENT}")
    if state.alert_manager and state.alert_manager.alerts:
        for a in state.alert_manager.alerts:
            direction = "≥" if a["direction"] == "above" else "≤"
            content.append(f"  {direction} ¥{a['price']:,.0f}\n", style=COLOR_WARN)
    else:
        content.append("  なし\n", style=COLOR_MUTED)

    return Panel(
        content,
        title=f"[bold {COLOR_TITLE}]ポジション[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def build_dashboard(state, width=120):
    """ダッシュボード全体を構築する"""
    chart_width = max(40, width - 42)

    header = build_header()
    price_row = build_price_panel(state)
    chart = build_chart_panel(state, width=chart_width)
    indicators = build_indicators_panel(state)
    position = build_position_panel(state)

    # 下段: 指標 + ポジション を横並び
    bottom_table = Table(
        show_header=False, show_edge=False, show_lines=False,
        box=None, padding=0, expand=True,
    )
    bottom_table.add_column(ratio=3)
    bottom_table.add_column(ratio=2)
    bottom_table.add_row(indicators, position)

    return Group(
        header,
        price_row,
        chart,
        bottom_table,
    )
