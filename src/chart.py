"""チャート・テクニカル指標モジュール"""
import requests

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


def fetch_klines(symbol="ETHUSDT", interval="1h", limit=100):
    """Binance APIからローソク足データを取得する"""
    try:
        resp = requests.get(
            BINANCE_KLINES_URL,
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def parse_closes(klines):
    """Klineデータから終値リストを抽出する"""
    return [float(k[4]) for k in klines]


def calc_sma(closes, period):
    """単純移動平均（SMA）を計算する"""
    result = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        result[i] = sum(closes[i - period + 1:i + 1]) / period
    return result


def calc_ema(closes, period):
    """指数移動平均（EMA）を計算する"""
    result = [None] * len(closes)
    if len(closes) < period:
        return result
    k = 2.0 / (period + 1)
    result[period - 1] = sum(closes[:period]) / period
    for i in range(period, len(closes)):
        result[i] = closes[i] * k + result[i - 1] * (1 - k)
    return result


def calc_rsi(closes, period=14):
    """RSIを計算する"""
    result = [None] * len(closes)
    if len(closes) < period + 1:
        return result

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100.0 - (100.0 / (1.0 + rs))

    return result


def calc_macd(closes, fast=12, slow=26, signal_period=9):
    """MACDを計算する（MACD線・シグナル線・ヒストグラム）"""
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)

    macd_line = [None] * len(closes)
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    macd_vals = [v if v is not None else 0.0 for v in macd_line]
    signal = calc_ema(macd_vals, signal_period)

    histogram = [None] * len(closes)
    for i in range(len(closes)):
        if macd_line[i] is not None and signal[i] is not None:
            histogram[i] = macd_line[i] - signal[i]

    return macd_line, signal, histogram


def render_candlestick(klines, width=60, height=20):
    """ターミナル内にローソク足チャートを描画する"""
    if not klines:
        return "データがありません"

    display_klines = klines[-width:]
    opens = [float(k[1]) for k in display_klines]
    highs = [float(k[2]) for k in display_klines]
    lows = [float(k[3]) for k in display_klines]
    closes = [float(k[4]) for k in display_klines]

    price_min = min(lows)
    price_max = max(highs)
    price_range = price_max - price_min
    if price_range == 0:
        price_range = 1.0

    grid = [[" " for _ in range(len(display_klines))] for _ in range(height)]

    for col, (o, h, low, c) in enumerate(zip(opens, highs, lows, closes)):
        h_row = height - 1 - int((h - price_min) / price_range * (height - 1))
        l_row = height - 1 - int((low - price_min) / price_range * (height - 1))
        o_row = height - 1 - int((o - price_min) / price_range * (height - 1))
        c_row = height - 1 - int((c - price_min) / price_range * (height - 1))

        for row in range(h_row, l_row + 1):
            if 0 <= row < height:
                grid[row][col] = "|"

        body_top = min(o_row, c_row)
        body_bot = max(o_row, c_row)
        char = "█" if c >= o else "░"
        for row in range(body_top, body_bot + 1):
            if 0 <= row < height:
                grid[row][col] = char

    lines = ["=" * (len(display_klines) + 16)]
    lines.append(f"  ETH/USDT ローソク足チャート（1H x {len(display_klines)}本）")
    lines.append("=" * (len(display_klines) + 16))

    for row in range(height):
        price_at_row = price_max - (row / (height - 1)) * price_range
        label = f"${price_at_row:>8.1f} "
        lines.append(label + "".join(grid[row]))

    lines.append("=" * (len(display_klines) + 16))
    return "\n".join(lines)


def format_indicators(closes):
    """テクニカル指標をフォーマットして表示する"""
    lines = [
        "=" * 50,
        "  テクニカル指標",
        "=" * 50,
    ]

    for period in [5, 13, 25]:
        sma = calc_sma(closes, period)
        val = sma[-1]
        if val is not None:
            lines.append(f"  SMA{period}: ${val:,.2f}")
        else:
            lines.append(f"  SMA{period}: データ不足")

    rsi = calc_rsi(closes, 14)
    rsi_val = rsi[-1]
    if rsi_val is not None:
        if rsi_val >= 70:
            status = "（買われすぎ）"
        elif rsi_val <= 30:
            status = "（売られすぎ）"
        else:
            status = ""
        lines.append(f"  RSI(14): {rsi_val:.1f} {status}")
    else:
        lines.append("  RSI(14): データ不足")

    macd_line, signal, histogram = calc_macd(closes)
    m = macd_line[-1]
    s = signal[-1]
    h = histogram[-1]
    if m is not None and s is not None:
        cross = "ゴールデンクロス" if m > s else "デッドクロス"
        lines.append(f"  MACD: {m:.2f}")
        lines.append(f"  Signal: {s:.2f}")
        lines.append(f"  Histogram: {h:.2f} ({cross})")
    else:
        lines.append("  MACD: データ不足")

    lines.append("=" * 50)
    return "\n".join(lines)
