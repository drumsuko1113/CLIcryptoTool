"""claude.ai連携モジュール"""
import subprocess
import webbrowser

CLAUDE_AI_URL = "https://claude.ai"


def generate_prompt(market_data):
    """現在の市場データからclaude.ai用プロンプトを生成する"""
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

以下の観点で分析してください：
1. 現在のトレンド方向と強さ
2. 重要なサポート/レジスタンスライン
3. エントリー/エグジットの推奨タイミング
4. リスク要因
5. 総合的な売買判断（買い/売り/様子見）"""

    return prompt


def copy_to_clipboard(text):
    """テキストをクリップボードにコピーする（Windows）"""
    process = subprocess.Popen(
        ["powershell", "-Command", "Set-Clipboard -Value $input"],
        stdin=subprocess.PIPE,
        creationflags=0x08000000
    )
    process.communicate(text.encode("utf-8"))


def open_claude_ai():
    """claude.aiをブラウザで開く"""
    webbrowser.open(CLAUDE_AI_URL)
