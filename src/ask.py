"""claude.ai連携モジュール"""
from src.platform_utils import copy_to_clipboard, open_url  # noqa: F401

CLAUDE_AI_URL = "https://claude.ai"


def _format_positions_section(positions, current_prices):
    """ポジションセクションを生成する（Issue #36）

    positions: list[dict]（entry_price / amount / currency を持つ）
    current_prices: dict {"USD": float, "JPY": float}
    """
    if not positions:
        return "【保有ポジション】\n- 現在ポジションなし\n"

    lines = ["【保有ポジション】"]
    # 各ポジション行
    for i, pos in enumerate(positions):
        cur = pos["currency"]
        sym = "$" if cur == "USD" else "¥"
        entry = pos["entry_price"]
        amt = pos["amount"]
        current = current_prices.get(cur, entry)
        pnl = (current - entry) * amt
        pnl_pct = ((current - entry) / entry * 100) if entry else 0.0
        sign = "+" if pnl >= 0 else ""
        lines.append(
            f"- [{i}] 仕入 {sym}{entry:,.2f} x {amt} ETH（{cur}建て）"
            f"→ 含み損益 {sign}{sym}{pnl:,.2f} ({sign}{pnl_pct:.2f}%)"
        )

    # 通貨ごとに 2 件以上あればサマリー
    currencies = []
    for p in positions:
        if p["currency"] not in currencies:
            currencies.append(p["currency"])

    for cur in currencies:
        target = [p for p in positions if p["currency"] == cur]
        if len(target) < 2:
            continue
        sym = "$" if cur == "USD" else "¥"
        total_amt = sum(p["amount"] for p in target)
        total_cost = sum(p["entry_price"] * p["amount"] for p in target)
        avg = total_cost / total_amt if total_amt else 0.0
        current = current_prices.get(cur, avg)
        market_value = current * total_amt
        pnl = market_value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost else 0.0
        sign = "+" if pnl >= 0 else ""
        lines.append(
            f"- {cur} 平均取得 {sym}{avg:,.2f} / 合計 {total_amt} ETH"
        )
        lines.append(
            f"- {cur} 全体含み損益: {sign}{sym}{pnl:,.2f} "
            f"({sign}{pnl_pct:.2f}%)"
        )

    return "\n".join(lines) + "\n"


def generate_prompt(market_data, positions=None, current_prices=None,
                    realized_profit=None):
    """現在の市場データからclaude.ai用プロンプトを生成する

    Issue #36: positions / current_prices / realized_profit を渡すと
    ポジション状況もプロンプトに反映する。
    """
    prompt = f"""あなたは暗号通貨のテクニカル分析の専門家です。
以下のETH（イーサリアム）の現在の市場データを分析し、
短期（1-3日）と中期（1-2週間）の見通しを日本語で教えてください。

【現在の市場データ】
- ETH/USD: ${market_data['eth_usd']:,.2f}
- ETH/JPY: ¥{market_data['eth_jpy']:,.0f}
- 24H変動: {market_data['change_percent']:+.2f}%

【テクニカル指標】
- RSI(14): {market_data['rsi']:.1f}
- MACD: {market_data['macd']:.2f}
- MACDシグナル: {market_data['signal']:.2f}
- SMA5: ${market_data['sma5']:,.2f}
- SMA13: ${market_data['sma13']:,.2f}
- SMA25: ${market_data['sma25']:,.2f}
"""

    # ポジション情報（Issue #36）
    if positions is not None:
        prices = current_prices or {
            "USD": market_data["eth_usd"],
            "JPY": market_data["eth_jpy"],
        }
        prompt += "\n" + _format_positions_section(positions, prices)
        if realized_profit is not None:
            prompt += f"- スイング累計実現益: ${realized_profit:,.2f}\n"

    prompt += """
以下の観点で分析してください：
1. 現在のトレンド方向と強さ
2. 重要なサポート/レジスタンスライン
3. エントリー/エグジットの推奨タイミング
4. リスク要因
5. 総合的な売買判断（買い/売り/様子見）"""

    if positions:
        prompt += """
6. 保有ポジションを保持/利確/損切りすべきか
7. 平均取得単価から見たナンピン/利確ラインの提案"""

    return prompt


def open_claude_ai():
    """claude.aiをブラウザで開く"""
    open_url(CLAUDE_AI_URL)
