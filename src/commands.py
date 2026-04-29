"""コマンドハンドラ - 各コマンドの実行ロジック"""
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from src.news import fetch_news, filter_iran_news
from src.analysis import analyze_market
from src.ask import generate_prompt, open_claude_ai
from src.platform_utils import copy_to_clipboard
from src.readme import build_readme
from src.dashboard import build_price_panel, build_chart_panel
from src.theme import (
    COLOR_BORDER, COLOR_TITLE, COLOR_MUTED, COLOR_ACCENT,
    COLOR_UP, COLOR_DOWN,
)

console = Console()


class CommandHandler:
    """コマンドハンド�� - 共有状態を保持してコマンドを実行する"""

    def __init__(self, market_state, alert_manager, position_manager,
                 refresh_fn, render_fn, data_lock):
        self.state = market_state
        self.alerts = alert_manager
        self.positions = position_manager
        self.refresh = refresh_fn
        self.render = render_fn
        self.lock = data_lock
        self._price_func = None

    def set_price_func(self, price_func):
        self._price_func = price_func

    def cmd_price(self, args):
        """価格パネルのみ表示（Issue #34）"""
        self.refresh()
        with self.lock:
            panel = build_price_panel(self.state)
        console.print(panel)

    def cmd_chart(self, args):
        """チャートパネルのみ表示（Issue #34）"""
        self.refresh()
        with self.lock:
            panel = build_chart_panel(self.state, width=console.width)
        console.print(panel)

    def cmd_news(self, args):
        console.print(f"\n  [bold {COLOR_ACCENT}]ニュースを取得中...[/]")
        entries = fetch_news(limit=10)
        console.print(_build_news_panel(entries, "最新ニュース", COLOR_TITLE, COLOR_ACCENT))

    def cmd_iran(self, args):
        console.print(f"\n  [bold {COLOR_ACCENT}]イラン関連ニュースを検索中...[/]")
        entries = fetch_news(limit=30)
        filtered = filter_iran_news(entries)
        console.print(_build_news_panel(filtered, "イラン関連ニュース", COLOR_DOWN, COLOR_DOWN))

    def cmd_analysis(self, args):
        if not self.state.has_data:
            self.refresh()

        with self.lock:
            closes = self.state.closes
            prices = self.state.prices

        if not closes or len(closes) < 26:
            console.print(f"  [{COLOR_DOWN}]データ不足です[/]")
            return

        indicators = {
            "rsi": self.state.rsi if self.state.rsi is not None else 50.0,
            "macd": self.state.macd if self.state.macd is not None else 0.0,
            "signal": self.state.signal if self.state.signal is not None else 0.0,
            "histogram": self.state.histogram if self.state.histogram is not None else 0.0,
            "sma5": _last_or(self.state.sma5, closes[-1]),
            "sma13": _last_or(self.state.sma13, closes[-1]),
            "sma25": _last_or(self.state.sma25, closes[-1]),
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

    def cmd_position(self, args):
        if args:
            subcmd = args[0].lower()
            if subcmd == "add":
                self._position_add(args[1:])
                return
            if subcmd == "remove":
                self._position_remove(args[1:])
                return
            if subcmd == "clear":
                self._position_clear()
                return
            console.print(
                f"  [{COLOR_DOWN}]不明なサブコマンド: {args[0]}[/]"
            )
            console.print(
                f"  [{COLOR_MUTED}]使い方: /position [add <価格> <数量> "
                f"[USD|JPY] | remove <番号> | clear][/]"
            )
            return

        if not self.state.prices:
            self.refresh()
        if not self.state.prices:
            console.print(f"  [{COLOR_DOWN}]価格取得失敗[/]")
            return
        output = self.positions.format_positions(
            self.state.prices["eth_usd"], self.state.prices["eth_jpy"]
        )
        panel = Panel(
            Text(output),
            title=f"[bold {COLOR_TITLE}]ポジション管理[/]",
            border_style=COLOR_BORDER,
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(panel)

    def _position_add(self, args):
        """/position add <価格> <数量> [USD|JPY]"""
        if len(args) < 2:
            console.print(
                f"  [{COLOR_DOWN}]使い方: /position add <価格> <数量> [USD|JPY][/]"
            )
            return
        try:
            price = float(args[0])
            amount = float(args[1])
        except ValueError:
            console.print(
                f"  [{COLOR_DOWN}]エラー: 価格・数量は数値で指定してください[/]"
            )
            return
        currency = args[2].upper() if len(args) >= 3 else "USD"
        if currency not in ("USD", "JPY"):
            console.print(
                f"  [{COLOR_DOWN}]エラー: 通貨は USD または JPY を指定してください[/]"
            )
            return
        self.positions.add_position(price, amount, currency)
        self.positions.save()
        sym = "$" if currency == "USD" else "¥"
        console.print(
            f"  [{COLOR_UP}]✓ ポジション追加: {sym}{price:,.2f} x {amount} ETH[/]"
        )

    def _position_remove(self, args):
        """/position remove <番号>"""
        if not args:
            console.print(f"  [{COLOR_DOWN}]使い方: /position remove <番号>[/]")
            return
        try:
            index = int(args[0])
        except ValueError:
            console.print(f"  [{COLOR_DOWN}]エラー: 番号は数値で指定してください[/]")
            return
        if self.positions.remove_position(index):
            self.positions.save()
            console.print(f"  [{COLOR_UP}]✓ ポジション [{index}] を削除しました[/]")
        else:
            console.print(
                f"  [{COLOR_DOWN}]エラー: 番号 {index} のポジションは存在しません[/]"
            )

    def _position_clear(self):
        """/position clear"""
        count = len(self.positions.positions)
        self.positions.clear_positions()
        self.positions.save()
        console.print(f"  [{COLOR_UP}]✓ {count}件のポジションを全削除しました[/]")

    def cmd_alert(self, args):
        if not args:
            console.print(self.alerts.format_alerts())
            return

        subcmd = args[0].lower()

        if subcmd == "remove":
            if len(args) < 2:
                console.print(f"  [{COLOR_DOWN}]使い方: /alert remove <番号>[/]")
                return
            try:
                index = int(args[1])
                if self.alerts.remove_alert(index):
                    console.print(f"  [{COLOR_UP}]✓ アラート [{index}] を削除しました[/]")
                else:
                    console.print(f"  [{COLOR_DOWN}]エラー: 番号 {index} のアラートは存在しません[/]")
            except ValueError:
                console.print(f"  [{COLOR_DOWN}]エラー: 番号は数値で指定してください[/]")
            return

        if subcmd == "clear":
            count = len(self.alerts.alerts)
            self.alerts.clear_alerts()
            console.print(f"  [{COLOR_UP}]✓ {count}件のアラートを全削除しました[/]")
            return

        try:
            price = float(subcmd)
            direction = args[1] if len(args) > 1 else "above"
            self.alerts.add_alert(price, direction)
            dir_label = "以上" if direction == "above" else "以下"
            console.print(f"  [{COLOR_UP}]✓ アラート設定: ¥{price:,.0f} {dir_label}[/]")
            if not self.alerts._running and self._price_func:
                self.alerts.start_monitor(self._price_func)
                console.print(f"  [{COLOR_ACCENT}]監視開始[/]")
        except ValueError:
            console.print(f"  [{COLOR_DOWN}]エラー: 価格は数値で指定してください[/]")
            console.print(
                f"  [{COLOR_MUTED}]使い方: /alert <価格> | /alert remove <番号> | /alert clear[/]"
            )

    def cmd_alerts(self, args):
        console.print(self.alerts.format_alerts())

    def cmd_ask(self, args):
        if not self.state.has_data:
            self.refresh()

        with self.lock:
            closes = self.state.closes
            prices = self.state.prices

        if not prices or not closes:
            console.print(f"  [{COLOR_DOWN}]データ取得失敗[/]")
            return

        market_data = {
            "eth_usd": prices["eth_usd"],
            "eth_jpy": prices["eth_jpy"],
            "change_percent": prices["change_percent"],
            "rsi": self.state.rsi if self.state.rsi is not None else 50.0,
            "macd": self.state.macd if self.state.macd is not None else 0.0,
            "signal": self.state.signal if self.state.signal is not None else 0.0,
            "sma5": _last_or(self.state.sma5, closes[-1]),
            "sma13": _last_or(self.state.sma13, closes[-1]),
            "sma25": _last_or(self.state.sma25, closes[-1]),
        }

        prompt = generate_prompt(
            market_data,
            positions=list(self.positions.positions),
            current_prices={
                "USD": prices["eth_usd"],
                "JPY": prices["eth_jpy"],
            },
            realized_profit=self.positions.total_profit,
        )
        copy_to_clipboard(prompt)
        open_claude_ai()
        console.print(f"  [{COLOR_UP}]✓ プロンプトをクリップボードにコピーしました[/]")
        console.print(f"  [{COLOR_ACCENT}]claude.ai を開きました。貼り付けて質問してください。[/]")

    def cmd_help(self, args):
        console.print(build_help_panel())

    def cmd_readme(self, args):
        section = args[0] if args else None
        console.print(build_readme(section))

    def cmd_quit(self, args):
        self.alerts.stop_monitor()
        console.print(f"\n  [{COLOR_ACCENT}]終了します。お疲れ様でした！[/]\n")
        sys.exit(0)

    def cmd_refresh(self, args):
        self.refresh()
        self.render()

    def get_commands_dict(self):
        """コマンド名とハンドラのマッピングを返す"""
        return {
            "price": self.cmd_price,
            "chart": self.cmd_chart,
            "news": self.cmd_news,
            "iran": self.cmd_iran,
            "analysis": self.cmd_analysis,
            "position": self.cmd_position,
            "alert": self.cmd_alert,
            "alerts": self.cmd_alerts,
            "ask": self.cmd_ask,
            "help": self.cmd_help,
            "readme": self.cmd_readme,
            "quit": self.cmd_quit,
            "refresh": self.cmd_refresh,
            "r": self.cmd_refresh,
        }


def _last_or(lst, default):
    """リストの末尾値を返す。None またはリスト空なら default。"""
    if lst and lst[-1] is not None:
        return lst[-1]
    return default


def _build_news_panel(entries, title, title_color, entry_color):
    """ニュース一覧をrichパネルで返す"""
    table = Table(
        show_header=False, border_style=COLOR_BORDER,
        box=box.ROUNDED, expand=True, padding=(0, 1),
    )
    table.add_column(ratio=1)

    if not entries:
        table.add_row(Text(f"  {title}はありません", style=COLOR_MUTED))
    else:
        for i, entry in enumerate(entries):
            text = Text()
            text.append(f"  [{i+1}] ", style=f"bold {entry_color}")
            text.append(f"{entry.title}\n", style="bold white")
            pub = getattr(entry, "published", "")
            text.append(f"      {pub}", style=COLOR_MUTED)
            table.add_row(text)

    return Panel(
        table,
        title=f"[bold {title_color}]{title}[/]",
        border_style=title_color,
        box=box.ROUNDED,
    )


def build_help_panel():
    """ヘルプをrichパネルで返す"""
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
        ("/position add <価格> <数量> [USD|JPY]", "ポジション追加"),
        ("/position remove <番号>", "ポジション削除"),
        ("/position clear", "ポジション全削除"),
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
