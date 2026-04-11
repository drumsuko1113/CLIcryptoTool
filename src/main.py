"""ETH Trading Terminal - メインREPL"""
import sys

from src.price import get_eth_prices, format_price_display
from src.chart import (
    fetch_klines, parse_closes, render_candlestick, format_indicators,
    calc_sma, calc_rsi, calc_macd,
)
from src.alert import AlertManager
from src.position import PositionManager
from src.news import fetch_news, filter_iran_news, format_news_display
from src.analysis import analyze_market
from src.ask import generate_prompt, copy_to_clipboard, open_claude_ai


WELCOME = """
╔══════════════════════════════════════════════════╗
║         ETH Trading Terminal v1.0                ║
║         ターミナルベース ETH トレード支援         ║
╚══════════════════════════════════════════════════╝

  /help でコマンド一覧を表示
"""

HELP_TEXT = """
  コマンド一覧:
  ─────────────────────────────────────
  /price      現在価格表示（ETH/JPY・ETH/USD）
  /chart      ローソク足チャート表示
  /news       最新ニュース取得
  /iran       イラン関連ニュースフィルタ
  /analysis   ルールベース自動分析
  /position   ポジション損益確認
  /alert <価格>  アラート設定（JPY）
  /alerts     アラート一覧表示
  /ask        claude.ai連携プロンプト生成
  /help       このヘルプを表示
  /quit       終了
  ─────────────────────────────────────
"""

alert_manager = AlertManager()
position_manager = PositionManager()


def parse_command(user_input):
    """ユーザー入力をコマンドと引数に分解する"""
    text = user_input.strip()
    if not text or not text.startswith("/"):
        return None, []
    parts = text[1:].split()
    cmd = parts[0] if parts else None
    args = parts[1:] if len(parts) > 1 else []
    return cmd, args


def cmd_price():
    """価格表示コマンド"""
    prices = get_eth_prices()
    if prices is None:
        print("  価格の取得に失敗しました。ネットワーク接続を確認してください。")
        return
    print(format_price_display(prices))


def cmd_chart():
    """チャート表示コマンド"""
    klines = fetch_klines()
    if not klines:
        print("  チャートデータの取得に失敗しました。")
        return
    print(render_candlestick(klines))
    closes = parse_closes(klines)
    print(format_indicators(closes))


def cmd_news():
    """ニュース表示コマンド"""
    print("  ニュースを取得中...")
    entries = fetch_news(limit=10)
    print(format_news_display(entries))


def cmd_iran():
    """イラン関連ニュース表示コマンド"""
    print("  イラン関連ニュースを検索中...")
    entries = fetch_news(limit=30)
    filtered = filter_iran_news(entries)
    print(format_news_display(filtered, title="イラン関連ニュース"))


def cmd_analysis():
    """自動分析コマンド"""
    klines = fetch_klines()
    if not klines:
        print("  データの取得に失敗しました。")
        return
    closes = parse_closes(klines)
    prices = get_eth_prices()

    rsi_vals = calc_rsi(closes, 14)
    macd_line, signal, histogram = calc_macd(closes)
    sma5 = calc_sma(closes, 5)
    sma13 = calc_sma(closes, 13)
    sma25 = calc_sma(closes, 25)

    indicators = {
        "rsi": rsi_vals[-1] if rsi_vals[-1] is not None else 50.0,
        "macd": macd_line[-1] if macd_line[-1] is not None else 0.0,
        "signal": signal[-1] if signal[-1] is not None else 0.0,
        "histogram": histogram[-1] if histogram[-1] is not None else 0.0,
        "sma5": sma5[-1] if sma5[-1] is not None else closes[-1],
        "sma13": sma13[-1] if sma13[-1] is not None else closes[-1],
        "sma25": sma25[-1] if sma25[-1] is not None else closes[-1],
        "current_price": closes[-1] if prices is None else prices["eth_usd"],
    }
    print(analyze_market(indicators))


def cmd_position():
    """ポジション表示コマンド"""
    prices = get_eth_prices()
    if prices is None:
        print("  価格の取得に失敗しました。")
        return
    print(position_manager.format_positions(prices["eth_usd"], prices["eth_jpy"]))


def cmd_alert(args):
    """アラート設定コマンド"""
    if not args:
        print(alert_manager.format_alerts())
        return
    try:
        price = float(args[0])
        direction = args[1] if len(args) > 1 else "above"
        alert_manager.add_alert(price, direction)
        print(f"  アラート設定: ¥{price:,.0f} {direction}")

        if not alert_manager._running:
            alert_manager.start_monitor(get_eth_prices)
            print("  価格監視を開始しました")
    except ValueError:
        print("  エラー: 価格は数値で指定してください")


def cmd_alerts():
    """アラート一覧表示コマンド"""
    print(alert_manager.format_alerts())


def cmd_ask():
    """claude.ai連携コマンド"""
    klines = fetch_klines()
    if not klines:
        print("  データの取得に失敗しました。")
        return
    closes = parse_closes(klines)
    prices = get_eth_prices()
    if prices is None:
        print("  価格の取得に失敗しました。")
        return

    rsi_vals = calc_rsi(closes, 14)
    macd_line, signal, _ = calc_macd(closes)
    sma5 = calc_sma(closes, 5)
    sma13 = calc_sma(closes, 13)
    sma25 = calc_sma(closes, 25)

    market_data = {
        "eth_usd": prices["eth_usd"],
        "eth_jpy": prices["eth_jpy"],
        "change_percent": prices["change_percent"],
        "rsi": rsi_vals[-1] if rsi_vals[-1] is not None else 50.0,
        "macd": macd_line[-1] if macd_line[-1] is not None else 0.0,
        "signal": signal[-1] if signal[-1] is not None else 0.0,
        "sma5": sma5[-1] if sma5[-1] is not None else closes[-1],
        "sma13": sma13[-1] if sma13[-1] is not None else closes[-1],
        "sma25": sma25[-1] if sma25[-1] is not None else closes[-1],
    }

    prompt = generate_prompt(market_data)
    copy_to_clipboard(prompt)
    open_claude_ai()
    print("  プロンプトをクリップボードにコピーしました")
    print("  claude.ai を開きました。貼り付けて質問してください。")


def cmd_help():
    """ヘルプ表示コマンド"""
    print(HELP_TEXT)


def cmd_quit():
    """終了コマンド"""
    alert_manager.stop_monitor()
    print("  終了します。お疲れ様でした！")
    sys.exit(0)


COMMANDS = {
    "price": lambda args: cmd_price(),
    "chart": lambda args: cmd_chart(),
    "news": lambda args: cmd_news(),
    "iran": lambda args: cmd_iran(),
    "analysis": lambda args: cmd_analysis(),
    "position": lambda args: cmd_position(),
    "alert": cmd_alert,
    "alerts": lambda args: cmd_alerts(),
    "ask": lambda args: cmd_ask(),
    "help": lambda args: cmd_help(),
    "quit": lambda args: cmd_quit(),
}


def main():
    """メインREPLループ"""
    print(WELCOME)

    while True:
        try:
            user_input = input("\n  ETH> ")
            cmd, args = parse_command(user_input)

            if cmd is None:
                continue

            if cmd in COMMANDS:
                COMMANDS[cmd](args)
            else:
                print(f"  不明なコマンド: /{cmd}")
                print("  /help でコマンド一覧を確認してください")

        except KeyboardInterrupt:
            print("\n")
            cmd_quit()
        except EOFError:
            cmd_quit()


if __name__ == "__main__":
    main()
