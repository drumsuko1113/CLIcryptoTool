"""ルールベース自動分析モジュール"""


def analyze_market(indicators):
    """テクニカル指標からルールベースで市場分析を行い、日本語で返す"""
    rsi = indicators["rsi"]
    macd = indicators["macd"]
    signal = indicators["signal"]
    histogram = indicators["histogram"]
    sma5 = indicators["sma5"]
    sma13 = indicators["sma13"]
    sma25 = indicators["sma25"]
    price = indicators["current_price"]

    lines = [
        "=" * 50,
        "  自動分析レポート",
        "=" * 50,
    ]

    # RSI分析
    lines.append("\n  【RSI分析】")
    if rsi >= 70:
        lines.append(f"  RSI: {rsi:.1f} → 買われすぎゾーン")
        lines.append("  → 短期的な調整・下落に注意")
    elif rsi <= 30:
        lines.append(f"  RSI: {rsi:.1f} → 売られすぎゾーン")
        lines.append("  → 反発の可能性あり")
    elif rsi >= 50:
        lines.append(f"  RSI: {rsi:.1f} → やや強気")
    else:
        lines.append(f"  RSI: {rsi:.1f} → やや弱気")

    # MACD分析
    lines.append("\n  【MACD分析】")
    if macd > signal:
        lines.append(f"  MACD: {macd:.2f} > Signal: {signal:.2f}")
        lines.append("  → ゴールデンクロス（買いシグナル）")
    else:
        lines.append(f"  MACD: {macd:.2f} < Signal: {signal:.2f}")
        lines.append("  → デッドクロス（売りシグナル）")

    if histogram > 0:
        lines.append(f"  ヒストグラム: {histogram:.2f}（上昇モメンタム）")
    else:
        lines.append(f"  ヒストグラム: {histogram:.2f}（下降モメンタム）")

    # 移動平均分析
    lines.append("\n  【移動平均分析】")
    if sma5 > sma13 > sma25:
        lines.append("  SMA5 > SMA13 > SMA25 → 強い上昇トレンド")
    elif sma5 < sma13 < sma25:
        lines.append("  SMA5 < SMA13 < SMA25 → 強い下降トレンド")
    else:
        lines.append("  移動平均線が交差中 → トレンド転換の可能性")

    if price > sma25:
        lines.append(f"  現在価格 ${price:,.2f} > SMA25 ${sma25:,.2f} → 上位推移")
    else:
        lines.append(f"  現在価格 ${price:,.2f} < SMA25 ${sma25:,.2f} → 下位推移")

    # 総合判断
    lines.append("\n  【総合判断】")
    bullish = 0
    if rsi > 50:
        bullish += 1
    if macd > signal:
        bullish += 1
    if sma5 > sma25:
        bullish += 1
    if price > sma25:
        bullish += 1

    if bullish >= 3:
        lines.append("  → 総合: 強気（買い優勢）")
    elif bullish <= 1:
        lines.append("  → 総合: 弱気（売り優勢）")
    else:
        lines.append("  → 総合: 中立（様子見推奨）")

    lines.append("")
    lines.append("  ※ これは自動分析であり投資助言ではありません")
    lines.append("=" * 50)
    return "\n".join(lines)
