"""コマンド補完モジュール - prompt_toolkit用"""
from prompt_toolkit.completion import Completer, Completion


COMMAND_DEFS = [
    ("price", "現在価格表示"),
    ("chart", "ローソク足チャート"),
    ("news", "最新ニュース取得"),
    ("iran", "イラン関連ニュース"),
    ("analysis", "ルールベース自動分析"),
    ("position", "ポジション損益確認"),
    ("alert", "アラート管理"),
    ("alerts", "アラート一覧"),
    ("ask", "claude.ai連携"),
    ("readme", "説明書表示"),
    ("refresh", "ダッシュボード更新"),
    ("help", "コマンド一覧"),
    ("quit", "終了"),
]

ALERT_SUBCOMMANDS = [
    ("remove", "アラート削除 (例: /alert remove 0)"),
    ("clear", "全アラート削除"),
]

README_SECTIONS = [
    ("overview", "全体概要"),
    ("price", "価格表示の見方"),
    ("chart", "チャートの見方"),
    ("indicators", "RSI・MACD・SMAの読み方"),
    ("alert", "アラート機能の使い方"),
    ("position", "ポジション管理の使い方"),
    ("news", "ニュース機能の使い方"),
    ("ask", "claude.ai連携の使い方"),
]


class EthCommandCompleter(Completer):
    """ETH Terminalのコマンド補完"""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # / で始まらない場合は補完しない
        if not text.startswith("/"):
            return

        parts = text[1:].split(" ", 1)
        cmd = parts[0]

        # サブコマンド補完: /alert <sub> または /readme <section>
        if len(parts) > 1:
            sub_text = parts[1].lstrip()

            if cmd == "alert":
                for name, desc in ALERT_SUBCOMMANDS:
                    if name.startswith(sub_text):
                        yield Completion(
                            name,
                            start_position=-len(sub_text),
                            display_meta=desc,
                        )
                return

            if cmd == "readme":
                for name, desc in README_SECTIONS:
                    if name.startswith(sub_text):
                        yield Completion(
                            name,
                            start_position=-len(sub_text),
                            display_meta=desc,
                        )
                return

            return

        # トップレベルコマンド補完
        for name, desc in COMMAND_DEFS:
            if name.startswith(cmd):
                yield Completion(
                    name,
                    start_position=-len(cmd),
                    display_meta=desc,
                )
