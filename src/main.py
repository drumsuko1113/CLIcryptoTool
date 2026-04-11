"""ETH Trading Terminal v2.0 - Bloomberg風ダッシュボードUI"""
import io
import sys
import threading
import time

# Windows cp932 エンコーディング問題を回避
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.formatted_text import HTML

from src.completer import EthCommandCompleter

from src.price import get_eth_prices
from src.chart import (
    fetch_klines, parse_closes,
    calc_sma, calc_rsi, calc_macd,
)
from src.alert import AlertManager
from src.position import PositionManager
from src.news import fetch_news, filter_iran_news
from src.analysis import analyze_market
from src.ask import generate_prompt, copy_to_clipboard, open_claude_ai
from src.dashboard import (
    MarketState, build_dashboard,
    COLOR_BORDER, COLOR_TITLE, COLOR_MUTED, COLOR_ACCENT,
    COLOR_UP, COLOR_DOWN,
)
from src.readme import build_readme

console = Console()
alert_manager = AlertManager()
position_manager = PositionManager()
market_state = MarketState()
market_state.position_manager = position_manager
market_state.alert_manager = alert_manager

# バックグラウンドデータ更新用
_data_lock = threading.Lock()
_refresh_flag = threading.Event()


def parse_command(user_input):
    """ユーザー入力をコマンドと引数に分解する"""
    text = user_input.strip()
    if not text or not text.startswith("/"):
        return None, []
    parts = text[1:].split()
    cmd = parts[0] if parts else None
    args = parts[1:] if len(parts) > 1 else []
    return cmd, args


def refresh_market_data():
    """市場データを最新に更新する"""
    try:
        prices = get_eth_prices()
        klines = fetch_klines(limit=80)
        closes = parse_closes(klines) if klines else []

        with _data_lock:
            if prices:
                market_state.prices = prices
            if klines:
                market_state.klines = klines
            if closes:
                market_state.closes = closes
            market_state.last_update = time.time()
    except Exception:
        pass


def _bg_refresh_loop(interval=15):
    """バックグラウンドでデータを定期更新するループ"""
    while True:
        refresh_market_data()
        _refresh_flag.set()
        time.sleep(interval)


def render_dashboard():
    """ダッシュボードを描画する"""
    width = console.width
    with _data_lock:
        dashboard = build_dashboard(market_state, width=width)
    console.clear()
    console.print(dashboard)


def _build_help_panel():
    """ヘルプをrichパネルで表示する"""
    table = Table(
        show_header=True, header_style=f"bold {COLOR_ACCENT}",
        border_style=COLOR_BORDER, box=box.SIMPLE_HEAVY,
        expand=True, padding=(0, 2),
    )
    table.add_column("コマンド", style=f"bold {COLOR_UP}", min_width=18)
    table.add_column("説明", style=COLOR_MUTED)

    commands = [
        ("/price", "現在価格表示"),
        ("/chart", "ローソク足チャート（フル表示）"),
        ("/news", "最新ニュース取得"),
        ("/iran", "イラン関連ニュースフィルタ"),
        ("/analysis", "ルールベース自動分析"),
        ("/position", "ポジション損益確認"),
        ("/alert <価格>", "アラート作成（JPY）"),
        ("/alert remove <番号>", "アラート削除"),
        ("/alert clear", "アラート全削除"),
        ("/alerts", "アラート一覧"),
        ("/ask", "claude.ai連携プロンプト生成"),
        ("/refresh", "ダッシュボード手動更新"),
        ("/readme [セクション]", "説明書（指標の読み方等）"),
        ("/help", "このヘルプを表示"),
        ("/quit", "終了"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    return Panel(
        table,
        title=f"[bold {COLOR_TITLE}]コマンド一覧[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(1, 1),
    )


def cmd_price():
    """価格表示コマンド"""
    refresh_market_data()
    render_dashboard()


def cmd_chart():
    """チャート表示コマンド（フル表示）"""
    refresh_market_data()
    render_dashboard()


def cmd_news():
    """ニュース表示コマンド"""
    console.print(f"\n  [bold {COLOR_ACCENT}]ニュースを取得中...[/]")
    entries = fetch_news(limit=10)

    table = Table(
        show_header=False, border_style=COLOR_BORDER,
        box=box.ROUNDED, expand=True, padding=(0, 1),
    )
    table.add_column(ratio=1)

    if not entries:
        table.add_row(Text("  ニュースはありません", style=COLOR_MUTED))
    else:
        for i, entry in enumerate(entries):
            text = Text()
            text.append(f"  [{i+1}] ", style=f"bold {COLOR_ACCENT}")
            text.append(f"{entry.title}\n", style="bold white")
            pub = getattr(entry, "published", "")
            text.append(f"      {pub}\n", style=COLOR_MUTED)
            text.append(f"      {entry.link}", style=COLOR_MUTED)
            table.add_row(text)

    panel = Panel(
        table,
        title=f"[bold {COLOR_TITLE}]最新ニュース[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
    )
    console.print(panel)


def cmd_iran():
    """イラン関連ニュース表示コマンド"""
    console.print(f"\n  [bold {COLOR_ACCENT}]イラン関連ニュースを検索中...[/]")
    entries = fetch_news(limit=30)
    filtered = filter_iran_news(entries)

    table = Table(
        show_header=False, border_style=COLOR_BORDER,
        box=box.ROUNDED, expand=True, padding=(0, 1),
    )
    table.add_column(ratio=1)

    if not filtered:
        table.add_row(Text("  イラン関連ニュースはありません", style=COLOR_MUTED))
    else:
        for i, entry in enumerate(filtered):
            text = Text()
            text.append(f"  [{i+1}] ", style=f"bold {COLOR_DOWN}")
            text.append(f"{entry.title}\n", style="bold white")
            pub = getattr(entry, "published", "")
            text.append(f"      {pub}", style=COLOR_MUTED)
            table.add_row(text)

    panel = Panel(
        table,
        title=f"[bold {COLOR_DOWN}]イラン関連ニュース[/]",
        border_style=COLOR_DOWN,
        box=box.ROUNDED,
    )
    console.print(panel)


def cmd_analysis():
    """自動分析コマンド"""
    if not market_state.has_data:
        refresh_market_data()

    with _data_lock:
        closes = market_state.closes
        prices = market_state.prices

    if not closes or len(closes) < 26:
        console.print(f"  [{COLOR_DOWN}]データ不足です[/]")
        return

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

    report = analyze_market(indicators)
    panel = Panel(
        Text(report),
        title=f"[bold {COLOR_TITLE}]自動分析レポート[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def cmd_position():
    """ポジション表示コマンド"""
    if not market_state.prices:
        refresh_market_data()
    if not market_state.prices:
        console.print(f"  [{COLOR_DOWN}]価格取得失敗[/]")
        return
    output = position_manager.format_positions(
        market_state.prices["eth_usd"], market_state.prices["eth_jpy"]
    )
    panel = Panel(
        Text(output),
        title=f"[bold {COLOR_TITLE}]ポジション管理[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def cmd_alert(args):
    """アラート設定コマンド（サブコマンド: remove, clear）"""
    if not args:
        console.print(alert_manager.format_alerts())
        return

    subcmd = args[0].lower()

    # /alert remove <index>
    if subcmd == "remove":
        if len(args) < 2:
            console.print(f"  [{COLOR_DOWN}]使い方: /alert remove <番号>[/]")
            return
        try:
            index = int(args[1])
            if alert_manager.remove_alert(index):
                console.print(f"  [{COLOR_UP}]✓ アラート [{index}] を削除しました[/]")
            else:
                console.print(f"  [{COLOR_DOWN}]エラー: 番号 {index} のアラートは存在しません[/]")
        except ValueError:
            console.print(f"  [{COLOR_DOWN}]エラー: 番号は数値で指定してください[/]")
        return

    # /alert clear
    if subcmd == "clear":
        count = len(alert_manager.alerts)
        alert_manager.clear_alerts()
        console.print(f"  [{COLOR_UP}]✓ {count}件のアラートを全削除しました[/]")
        return

    # /alert <価格> [above|below] — 新規作成
    try:
        price = float(subcmd)
        direction = args[1] if len(args) > 1 else "above"
        alert_manager.add_alert(price, direction)
        dir_label = "以上" if direction == "above" else "以下"
        console.print(
            f"  [{COLOR_UP}]✓ アラート設定: ¥{price:,.0f} {dir_label}[/]"
        )
        if not alert_manager._running:
            alert_manager.start_monitor(get_eth_prices)
            console.print(f"  [{COLOR_ACCENT}]監視開始[/]")
    except ValueError:
        console.print(f"  [{COLOR_DOWN}]エラー: 価格は数値で指定してください[/]")
        console.print(f"  [{COLOR_MUTED}]使い方: /alert <価格> | /alert remove <番号> | /alert clear[/]")


def cmd_alerts():
    """アラート一覧表示コマンド"""
    console.print(alert_manager.format_alerts())


def cmd_ask():
    """claude.ai連携コマンド"""
    if not market_state.has_data:
        refresh_market_data()

    with _data_lock:
        closes = market_state.closes
        prices = market_state.prices

    if not prices or not closes:
        console.print(f"  [{COLOR_DOWN}]データ取得失敗[/]")
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
    console.print(f"  [{COLOR_UP}]✓ プロンプトをクリップボードにコピーしました[/]")
    console.print(f"  [{COLOR_ACCENT}]claude.ai を開きました。貼り付けて質問してください。[/]")


def cmd_help():
    """ヘルプ表示コマンド"""
    console.print(_build_help_panel())


def cmd_readme(args):
    """説明書表示コマンド"""
    section = args[0] if args else None
    console.print(build_readme(section))


def cmd_quit():
    """終了コマンド"""
    alert_manager.stop_monitor()
    console.print(f"\n  [{COLOR_ACCENT}]終了します。お疲れ様でした！[/]\n")
    sys.exit(0)


def cmd_refresh():
    """ダッシュボード手動更新コマンド"""
    refresh_market_data()
    render_dashboard()


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
    "readme": cmd_readme,
    "quit": lambda args: cmd_quit(),
    "refresh": lambda args: cmd_refresh(),
    "r": lambda args: cmd_refresh(),
}


_completer = EthCommandCompleter()


def _prompt_input():
    """コマンドプロンプトを表示して入力を受け付ける（補完付き）"""
    try:
        console.print(
            f"\n  [{COLOR_BORDER}]─────────────────────────────────────[/]"
        )
        user_input = pt_prompt(
            HTML("<b><skyblue>  ETH&gt; </skyblue></b>"),
            completer=_completer,
            complete_while_typing=True,
        )
        return user_input
    except (KeyboardInterrupt, EOFError):
        return "/quit"


def main():
    """メインREPLループ（ダッシュボードUI）"""
    # バックグラウンドデータ更新スレッド開始
    bg_thread = threading.Thread(target=_bg_refresh_loop, args=(15,), daemon=True)
    bg_thread.start()

    # 初期データ取得を待つ
    console.print(f"\n  [bold {COLOR_ACCENT}]◆ ETH TRADING TERMINAL v2.0[/]")
    console.print(f"  [{COLOR_MUTED}]データを取得中...[/]\n")
    _refresh_flag.wait(timeout=15)

    # 初回ダッシュボード描画
    render_dashboard()

    while True:
        user_input = _prompt_input()
        cmd, args = parse_command(user_input)

        if cmd is None:
            # 空Enter → ダッシュボード再描画
            if _refresh_flag.is_set():
                _refresh_flag.clear()
            render_dashboard()
            continue

        if cmd in COMMANDS:
            COMMANDS[cmd](args)
        else:
            console.print(
                f"  [{COLOR_DOWN}]不明なコマンド: /{cmd}[/]  "
                f"[{COLOR_MUTED}]/help でコマンド一覧を確認[/]"
            )


if __name__ == "__main__":
    main()
