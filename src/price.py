"""ETH価格取得モジュール（Binance公開API使用）"""
import requests

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
EXCHANGE_RATE_URL = "https://open.er-api.com/v6/latest/USD"


def fetch_eth_usdt_ticker():
    """Binance APIからETH/USDTの24hティッカーを取得する"""
    try:
        resp = requests.get(
            BINANCE_TICKER_URL,
            params={"symbol": "ETHUSDT"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_usd_jpy_rate():
    """USD/JPY為替レートを取得する"""
    try:
        resp = requests.get(EXCHANGE_RATE_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["rates"]["JPY"]
    except Exception:
        return None


def get_eth_prices():
    """ETH/USDとETH/JPYの価格情報を統合して返す"""
    ticker = fetch_eth_usdt_ticker()
    if ticker is None:
        return None

    rate = fetch_usd_jpy_rate()
    if rate is None:
        rate = 150.0  # フォールバック

    eth_usd = float(ticker["lastPrice"])
    high_usd = float(ticker["highPrice"])
    low_usd = float(ticker["lowPrice"])
    volume = float(ticker["volume"])
    change_percent = float(ticker["priceChangePercent"])

    return {
        "eth_usd": eth_usd,
        "eth_jpy": eth_usd * rate,
        "high_usd": high_usd,
        "low_usd": low_usd,
        "high_jpy": high_usd * rate,
        "low_jpy": low_usd * rate,
        "volume": volume,
        "change_percent": change_percent,
        "usd_jpy_rate": rate,
    }


def format_price_display(prices):
    """価格情報を見やすくフォーマットして返す"""
    lines = [
        "=" * 50,
        "  ETH 価格情報",
        "=" * 50,
        f"  ETH/USD:  ${prices['eth_usd']:,.2f}",
        f"  ETH/JPY:  ¥{prices['eth_jpy']:,.0f}",
        f"  USD/JPY:  ¥{prices['usd_jpy_rate']:.2f}",
        "-" * 50,
        f"  24H 高値: ${prices['high_usd']:,.2f} (¥{prices['high_jpy']:,.0f})",
        f"  24H 安値: ${prices['low_usd']:,.2f} (¥{prices['low_jpy']:,.0f})",
        f"  24H 出来高: {prices['volume']:,.2f} ETH",
        f"  24H 変動: {prices['change_percent']:+.2f}%",
        "=" * 50,
    ]
    return "\n".join(lines)
