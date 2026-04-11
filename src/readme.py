"""説明書モジュール - 各機能の使い方・指標の読み方"""
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich import box

from src.theme import (
    COLOR_BORDER, COLOR_TITLE, COLOR_ACCENT, COLOR_MUTED,
    COLOR_UP, COLOR_DOWN,
)


def _section(title, content):
    return Panel(
        content,
        title=f"[bold {COLOR_TITLE}]{title}[/]",
        border_style=COLOR_BORDER,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _build_overview():
    t = Text()
    t.append("ETH Trading Terminal", style=f"bold {COLOR_ACCENT}")
    t.append(" は、ターミナル上で動作する ETH トレード支援ツールです。\n\n", style="white")
    t.append("主な機能:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  • リアルタイム価格表示（ETH/JPY・ETH/USD）\n", style="white")
    t.append("  • ローソク足チャート＋テクニカル指標\n", style="white")
    t.append("  • 価格アラート（Windows通知）\n", style="white")
    t.append("  • ポジション管理・損益計算\n", style="white")
    t.append("  • 暗号通貨ニュース取得\n", style="white")
    t.append("  • AI分析連携（claude.ai）\n\n", style="white")
    t.append("データソース:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  • 価格: Binance公開API（無料・登録不要）\n", style="white")
    t.append("  • 為替: Open Exchange Rates API\n", style="white")
    t.append("  • ニュース: CoinDesk・Cointelegraph RSS\n\n", style="white")
    t.append("セクション別の詳細は ", style=COLOR_MUTED)
    t.append("/readme <セクション名>", style=f"bold {COLOR_UP}")
    t.append(" で確認できます。\n", style=COLOR_MUTED)
    t.append("例: /readme chart  /readme indicators  /readme alert\n", style=COLOR_MUTED)

    table = Table(
        show_header=True, header_style=f"bold {COLOR_ACCENT}",
        box=box.SIMPLE, padding=(0, 2),
    )
    table.add_column("セクション名", style=f"bold {COLOR_UP}", min_width=14)
    table.add_column("内容", style="white")
    table.add_row("overview", "この画面（全体説明）")
    table.add_row("price", "価格表示の見方")
    table.add_row("chart", "ローソク足チャートの見方")
    table.add_row("indicators", "テクニカル指標（RSI・MACD・SMA）の読み方")
    table.add_row("alert", "アラート機能の使い方")
    table.add_row("position", "ポジション管理の使い方")
    table.add_row("news", "ニュース機能の使い方")
    table.add_row("ask", "claude.ai連携の使い方")

    return _section("📖 説明書 - 全体概要", Group(t, table))


def _build_price():
    t = Text()
    t.append("/price コマンド\n\n", style=f"bold {COLOR_ACCENT}")
    t.append("ETHの現在価格をリアルタイムで表示します。\n\n", style="white")

    t.append("表示項目:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  ETH/JPY   ", style=f"bold {COLOR_UP}")
    t.append("日本円換算の価格\n", style="white")
    t.append("  ETH/USD   ", style=f"bold {COLOR_UP}")
    t.append("米ドル建ての価格\n", style="white")
    t.append("  ▲ / ▼     ", style=f"bold {COLOR_UP}")
    t.append("24時間の変動率（", style="white")
    t.append("シアン=上昇", style=COLOR_UP)
    t.append("、", style="white")
    t.append("赤=下落", style=COLOR_DOWN)
    t.append("）\n", style="white")
    t.append("  24H H/L   ", style=f"bold {COLOR_UP}")
    t.append("24時間の最高値・最安値\n", style="white")
    t.append("  Volume    ", style=f"bold {COLOR_UP}")
    t.append("24時間の取引量（ETH単位）\n", style="white")
    t.append("  USD/JPY   ", style=f"bold {COLOR_UP}")
    t.append("ドル円レート（価格換算に使用）\n\n", style="white")

    t.append("ダッシュボード上部に常時表示され、15秒ごとに自動更新されます。\n", style=COLOR_MUTED)

    return _section("💰 価格表示", t)


def _build_chart():
    t = Text()
    t.append("/chart コマンド\n\n", style=f"bold {COLOR_ACCENT}")
    t.append("ターミナル内にローソク足チャートを描画します。\n\n", style="white")

    t.append("ローソク足の読み方:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  ┃ ", style=f"bold {COLOR_UP}")
    t.append("シアンの実体 → 陽線（終値 > 始値 = 上昇）\n", style="white")
    t.append("  ┃ ", style=f"bold {COLOR_DOWN}")
    t.append("赤の実体     → 陰線（終値 < 始値 = 下落）\n", style="white")
    t.append("  │ ", style=COLOR_MUTED)
    t.append("ヒゲ         → その時間帯の高値・安値\n\n", style="white")

    t.append("移動平均線（SMA）:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  · ", style="bold #66bb6a")
    t.append("SMA5（緑）   → 短期トレンド（5本平均）\n", style="white")
    t.append("  · ", style="bold #ab47bc")
    t.append("SMA13（紫）  → 中期トレンド（13本平均）\n", style="white")
    t.append("  · ", style="bold #ffab40")
    t.append("SMA25（橙）  → 長期トレンド（25本平均）\n\n", style="white")

    t.append("見方のコツ:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  • SMA5 > SMA13 > SMA25 → 強い上昇トレンド\n", style="white")
    t.append("  • SMA5 < SMA13 < SMA25 → 強い下降トレンド\n", style="white")
    t.append("  • SMAが交差 → トレンド転換のサイン\n", style="white")
    t.append("  • 価格がSMA25より上 → 上位推移（強気）\n", style="white")
    t.append("  • 価格がSMA25より下 → 下位推移（弱気）\n", style="white")

    return _section("📊 チャートの見方", t)


def _build_indicators():
    t = Text()
    t.append("ダッシュボード下部に常時表示されるテクニカル指標の読み方です。\n\n", style="white")

    # RSI
    t.append("━━━ RSI（相対力指数）━━━\n", style=f"bold {COLOR_ACCENT}")
    t.append("「買われすぎ」「売られすぎ」を0〜100で示す指標。\n\n", style="white")
    t.append("  70以上  ", style=f"bold {COLOR_DOWN}")
    t.append("→ 買われすぎ（短期的に下落の可能性）\n", style="white")
    t.append("  30以下  ", style=f"bold {COLOR_UP}")
    t.append("→ 売られすぎ（反発の可能性）\n", style="white")
    t.append("  50付近  ", style=f"bold {COLOR_MUTED}")
    t.append("→ 中立\n\n", style="white")
    t.append("  ゲージバーの色: ", style=COLOR_MUTED)
    t.append("シアン", style=COLOR_UP)
    t.append("=低い  ", style=COLOR_MUTED)
    t.append("青", style=COLOR_ACCENT)
    t.append("=中立  ", style=COLOR_MUTED)
    t.append("赤", style=COLOR_DOWN)
    t.append("=高い\n\n", style=COLOR_MUTED)

    # MACD
    t.append("━━━ MACD ━━━\n", style=f"bold {COLOR_ACCENT}")
    t.append("トレンドの方向と勢いを示す指標。\n\n", style="white")
    t.append("  ▲ GC（ゴールデンクロス）", style=f"bold {COLOR_UP}")
    t.append(" → MACD > Signal → 買いシグナル\n", style="white")
    t.append("  ▼ DC（デッドクロス）    ", style=f"bold {COLOR_DOWN}")
    t.append(" → MACD < Signal → 売りシグナル\n\n", style="white")
    t.append("  Histogram（ヒストグラム）:\n", style="white")
    t.append("    プラスで拡大中 → 上昇の勢いが加速\n", style="white")
    t.append("    マイナスで拡大中 → 下落の勢いが加速\n", style="white")
    t.append("    ゼロに近づく → トレンド転換の可能性\n\n", style="white")

    # SMA
    t.append("━━━ 移動平均（SMA）━━━\n", style=f"bold {COLOR_ACCENT}")
    t.append("一定期間の終値平均。トレンドの方向を確認するのに使います。\n\n", style="white")
    t.append("  SMA5   ", style="bold #66bb6a")
    t.append("短期（直近5時間の平均）\n", style="white")
    t.append("  SMA13  ", style="bold #ab47bc")
    t.append("中期（直近13時間の平均）\n", style="white")
    t.append("  SMA25  ", style="bold #ffab40")
    t.append("長期（直近25時間の平均）\n\n", style="white")
    t.append("  現在価格とSMAの位置関係で、トレンドの強さを判断します。\n", style=COLOR_MUTED)

    return _section("📈 テクニカル指標の読み方", t)


def _build_alert():
    t = Text()
    t.append("価格が指定値に到達したらWindows通知でお知らせする機能です。\n\n", style="white")

    t.append("コマンド一覧:\n", style=f"bold {COLOR_ACCENT}")

    table = Table(
        show_header=True, header_style=f"bold {COLOR_ACCENT}",
        box=box.SIMPLE, padding=(0, 2),
    )
    table.add_column("コマンド", style=f"bold {COLOR_UP}", min_width=26)
    table.add_column("説明", style="white")
    table.add_row("/alert 350000", "¥350,000以上でアラート作成")
    table.add_row("/alert 300000 below", "¥300,000以下でアラート作成")
    table.add_row("/alert remove 0", "番号0のアラートを削除")
    table.add_row("/alert clear", "全アラートを一括削除")
    table.add_row("/alerts", "設定中のアラート一覧表示")

    t2 = Text()
    t2.append("\n仕組み:\n", style=f"bold {COLOR_ACCENT}")
    t2.append("  • 最初のアラート設定時にバックグラウンド監視が自動開始\n", style="white")
    t2.append("  • 10秒間隔で価格をチェック\n", style="white")
    t2.append("  • 条件に到達するとWindows通知を表示\n", style="white")
    t2.append("  • 発火したアラートは自動的に削除される\n", style="white")
    t2.append("  • 複数のアラートを同時に管理可能\n\n", style="white")
    t2.append("番号は /alerts で表示される [0] [1] のインデックスです。\n", style=COLOR_MUTED)

    return _section("🔔 アラート機能", Group(t, table, t2))


def _build_position():
    t = Text()
    t.append("仕入れ値と数量を登録して含み損益をリアルタイム計算する機能です。\n\n", style="white")

    t.append("コマンド:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  /position", style=f"bold {COLOR_UP}")
    t.append("  → ポジション一覧と損益を表示\n\n", style="white")

    t.append("表示の見方:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  $2,000.00 x1.5  ", style=COLOR_MUTED)
    t.append("+$360.00 (+12.0%)\n", style=COLOR_UP)
    t.append("  ↑仕入値 ↑数量    ↑含み損益   ↑損益率\n\n", style=COLOR_MUTED)

    t.append("  ", style="")
    t.append("シアン", style=COLOR_UP)
    t.append(" = 含み益  ", style="white")
    t.append("赤", style=COLOR_DOWN)
    t.append(" = 含み損\n\n", style="white")

    t.append("  累計: ", style=COLOR_MUTED)
    t.append("スイングトレードの確定利益の合計\n\n", style="white")

    t.append("設定方法:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  config/position.json を直接編集するか、\n", style="white")
    t.append("  プログラムから PositionManager を使って登録します。\n", style="white")
    t.append("  ダッシュボード右下にも常時表示されます。\n", style=COLOR_MUTED)

    return _section("💼 ポジション管理", t)


def _build_news():
    t = Text()
    t.append("暗号通貨関連のニュースをRSSフィードから取得する機能です。\n\n", style="white")

    t.append("コマンド:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  /news", style=f"bold {COLOR_UP}")
    t.append("    → CoinDesk・Cointelegraphの最新ニュース10件\n", style="white")
    t.append("  /iran", style=f"bold {COLOR_UP}")
    t.append("    → イラン関連ニュースのみフィルタ表示\n\n", style="white")

    t.append("/iran フィルタキーワード:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  iran, イラン, tehran, テヘラン, sanctions, 制裁 など\n\n", style="white")

    t.append("地政学リスクの把握に活用してください。\n", style=COLOR_MUTED)
    t.append("ニュースは取得時点の最新順で表示されます。\n", style=COLOR_MUTED)

    return _section("📰 ニュース機能", t)


def _build_ask():
    t = Text()
    t.append("現在の市場データを含むプロンプトを自動生成し、\n", style="white")
    t.append("claude.ai に貼り付けて AI に分析を依頼する機能です。\n\n", style="white")

    t.append("使い方:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  1. /ask と入力\n", style="white")
    t.append("  2. 自動的にプロンプトがクリップボードにコピーされる\n", style="white")
    t.append("  3. ブラウザで claude.ai が開く\n", style="white")
    t.append("  4. Ctrl+V で貼り付けて送信\n\n", style="white")

    t.append("プロンプトに含まれる情報:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  • ETH/USD・ETH/JPY 現在価格\n", style="white")
    t.append("  • 24H変動率\n", style="white")
    t.append("  • RSI(14)\n", style="white")
    t.append("  • MACD・シグナル値\n", style="white")
    t.append("  • SMA5/13/25\n\n", style="white")

    t.append("AI に聞く分析の観点:\n", style=f"bold {COLOR_ACCENT}")
    t.append("  • トレンド方向と強さ\n", style="white")
    t.append("  • サポート/レジスタンスライン\n", style="white")
    t.append("  • エントリー/エグジットのタイミング\n", style="white")
    t.append("  • リスク要因\n", style="white")
    t.append("  • 総合的な売買判断\n", style="white")

    return _section("🤖 claude.ai 連携", t)


SECTIONS = {
    "overview": _build_overview,
    "price": _build_price,
    "chart": _build_chart,
    "indicators": _build_indicators,
    "alert": _build_alert,
    "position": _build_position,
    "news": _build_news,
    "ask": _build_ask,
}


def build_readme(section=None):
    """説明書を構築する。sectionが指定されればそのセクションのみ返す。"""
    if section is None:
        return _build_overview()

    if section in SECTIONS:
        return SECTIONS[section]()

    # 不明なセクション
    t = Text()
    t.append(f"  セクション '{section}' は存在しません。\n\n", style=COLOR_DOWN)
    t.append("  利用可能なセクション: ", style=COLOR_MUTED)
    t.append(", ".join(SECTIONS.keys()), style=f"bold {COLOR_UP}")
    return Panel(
        t,
        title=f"[bold {COLOR_DOWN}]エラー[/]",
        border_style=COLOR_DOWN,
        box=box.ROUNDED,
        padding=(1, 2),
    )
