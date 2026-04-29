"""ETH Trading Terminal v2.0 - メインREPLエントリポイント"""
import io
import sys
import threading
import time

# Windows cp932 エンコーディング問題を回避
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.formatted_text import HTML

from src.completer import EthCommandCompleter
from src.price import get_eth_prices
from src.chart import fetch_klines, parse_closes
from src.alert import AlertManager
from src.position import PositionManager
from src.dashboard import MarketState, build_dashboard
from src.commands import CommandHandler
from src.theme import COLOR_BORDER, COLOR_MUTED, COLOR_ACCENT, COLOR_DOWN

console = Console()
alert_manager = AlertManager()
position_manager = PositionManager()
# Issue #37: 長期保有用ポジションは別ファイルで永続化
long_position_manager = PositionManager("config/long_position.json")
market_state = MarketState()
market_state.position_manager = position_manager
market_state.alert_manager = alert_manager

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
            market_state.compute_indicators()
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


# コマンドハンドラを初期化
handler = CommandHandler(
    market_state=market_state,
    alert_manager=alert_manager,
    position_manager=position_manager,
    refresh_fn=refresh_market_data,
    render_fn=render_dashboard,
    data_lock=_data_lock,
    long_position_manager=long_position_manager,
)
handler.set_price_func(get_eth_prices)
COMMANDS = handler.get_commands_dict()

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
    """メインREPLループ"""
    bg_thread = threading.Thread(target=_bg_refresh_loop, args=(15,), daemon=True)
    bg_thread.start()

    console.print(f"\n  [bold {COLOR_ACCENT}]◆ ETH TRADING TERMINAL v2.0[/]")
    console.print(f"  [{COLOR_MUTED}]データを取得中...[/]\n")
    _refresh_flag.wait(timeout=15)

    render_dashboard()

    while True:
        user_input = _prompt_input()
        cmd, args = parse_command(user_input)

        if cmd is None:
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
