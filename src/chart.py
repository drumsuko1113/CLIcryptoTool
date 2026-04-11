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
