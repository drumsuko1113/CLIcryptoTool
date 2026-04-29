"""ポジション管理モジュール"""
import json
import os
from datetime import datetime


class PositionManager:
    """ポジション（建玉）を管理するクラス"""

    def __init__(self, config_path="config/position.json"):
        self.config_path = config_path
        self.positions = []
        self.trade_history = []
        self.total_profit = 0.0
        self.load()

    def add_position(self, entry_price, amount, currency="USD"):
        """ポジションを追加する"""
        self.positions.append({
            "entry_price": entry_price,
            "amount": amount,
            "currency": currency,
            "date": datetime.now().isoformat(),
        })

    def remove_position(self, index):
        """ポジションを削除する"""
        if 0 <= index < len(self.positions):
            self.positions.pop(index)
            return True
        return False

    def clear_positions(self):
        """全ポジションを削除する（取引履歴・累計利益は保持）"""
        self.positions = []

    def _by_currency(self, currency):
        """指定通貨のポジションだけを返す"""
        return [p for p in self.positions if p["currency"] == currency]

    def avg_entry_price(self, currency):
        """通貨内の加重平均取得単価を返す。該当ポジションが無ければ None"""
        target = self._by_currency(currency)
        if not target:
            return None
        total_cost = sum(p["entry_price"] * p["amount"] for p in target)
        total_amt = sum(p["amount"] for p in target)
        if total_amt == 0:
            return None
        return total_cost / total_amt

    def total_amount(self, currency):
        """通貨内の合計保有数量"""
        return sum(p["amount"] for p in self._by_currency(currency))

    def total_unrealized_pnl(self, current_price, currency):
        """通貨内の全体含み損益と損益率を返す"""
        target = self._by_currency(currency)
        if not target:
            return {"pnl": 0.0, "pnl_percent": 0.0}
        cost = sum(p["entry_price"] * p["amount"] for p in target)
        market_value = sum(current_price * p["amount"] for p in target)
        pnl = market_value - cost
        pnl_percent = (pnl / cost * 100) if cost else 0.0
        return {"pnl": pnl, "pnl_percent": pnl_percent}

    def currencies_in_use(self):
        """ポジションが存在する通貨の一覧（重複除去）"""
        seen = []
        for p in self.positions:
            if p["currency"] not in seen:
                seen.append(p["currency"])
        return seen

    def calc_pnl(self, index, current_price):
        """指定ポジションの含み損益を計算する"""
        pos = self.positions[index]
        entry = pos["entry_price"]
        amount = pos["amount"]
        pnl = (current_price - entry) * amount
        pnl_percent = ((current_price - entry) / entry) * 100
        return {
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "entry_price": entry,
            "current_price": current_price,
            "amount": amount,
        }

    def record_trade(self, profit, currency="USD"):
        """決済した利益を記録する"""
        self.trade_history.append({
            "profit": profit,
            "currency": currency,
            "date": datetime.now().isoformat(),
        })
        self.total_profit += profit

    def save(self):
        """ポジション・履歴をファイルに保存する"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {
            "positions": self.positions,
            "trade_history": self.trade_history,
            "total_profit": self.total_profit,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """ファイルからポジション・履歴を読み込む"""
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.positions = data.get("positions", [])
            self.trade_history = data.get("trade_history", [])
            self.total_profit = data.get("total_profit", 0.0)
        except (json.JSONDecodeError, KeyError):
            pass

    def format_positions(self, current_usd, current_jpy,
                         title="ポジション管理", include_footer=True):
        """ポジション情報をフォーマットして返す

        title: セクション見出し（Issue #37: 長期保有との区別用）
        include_footer: スイング累計利益・取引回数の行を含めるか
            （長期セクションでは False で抑制）
        """
        lines = [
            "=" * 50,
            f"  {title}",
            "=" * 50,
        ]

        if not self.positions:
            lines.append("  ポジション: なし")
        else:
            for i, pos in enumerate(self.positions):
                entry = pos["entry_price"]
                amount = pos["amount"]
                currency = pos["currency"]

                if currency == "USD":
                    current = current_usd
                    symbol = "$"
                else:
                    current = current_jpy
                    symbol = "¥"

                pnl = self.calc_pnl(i, current)
                sign = "+" if pnl["pnl"] >= 0 else ""
                lines.append(
                    f"  [{i}] 仕入: {symbol}{entry:,.2f} x {amount} ETH"
                )
                lines.append(
                    f"      現在: {symbol}{current:,.2f} | "
                    f"損益: {sign}{symbol}{pnl['pnl']:,.2f} "
                    f"({sign}{pnl['pnl_percent']:.2f}%)"
                )

        # 通貨ごとに >= 2 件あれば集計サマリーを出す（Issue #35）
        for cur in self.currencies_in_use():
            target = self._by_currency(cur)
            if len(target) < 2:
                continue
            symbol = "$" if cur == "USD" else "¥"
            current_price = current_usd if cur == "USD" else current_jpy
            avg = self.avg_entry_price(cur)
            total_amt = self.total_amount(cur)
            agg = self.total_unrealized_pnl(current_price, cur)
            sign = "+" if agg["pnl"] >= 0 else ""
            lines.append("-" * 50)
            lines.append(
                f"  {cur} 合計: {total_amt} ETH | "
                f"平均取得 {symbol}{avg:,.2f}"
            )
            lines.append(
                f"  含み損益: {sign}{symbol}{agg['pnl']:,.2f} "
                f"({sign}{agg['pnl_percent']:.2f}%)"
            )

        if include_footer:
            lines.append("-" * 50)
            lines.append(f"  スイング累計利益: ${self.total_profit:,.2f}")
            lines.append(f"  取引回数: {len(self.trade_history)}回")
        lines.append("=" * 50)
        return "\n".join(lines)
