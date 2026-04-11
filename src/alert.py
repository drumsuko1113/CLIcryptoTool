"""アラート管理モジュール"""
import threading
import time


class AlertManager:
    """価格アラートを管理するクラス"""

    def __init__(self):
        self.alerts = []
        self._monitor_thread = None
        self._running = False

    def add_alert(self, price, direction="above"):
        """アラートを追加する"""
        self.alerts.append({
            "price": price,
            "direction": direction,
            "triggered": False,
        })

    def remove_alert(self, index):
        """指定インデックスのアラートを削除する"""
        if 0 <= index < len(self.alerts):
            self.alerts.pop(index)
            return True
        return False

    def check_alerts(self, current_price):
        """現在価格でアラート条件をチェックし、発火したアラートを返す"""
        triggered = []
        remaining = []

        for alert in self.alerts:
            if alert["direction"] == "above" and current_price >= alert["price"]:
                triggered.append(alert)
            elif alert["direction"] == "below" and current_price <= alert["price"]:
                triggered.append(alert)
            else:
                remaining.append(alert)

        self.alerts = remaining
        return triggered

    def format_alerts(self):
        """アラート一覧をフォーマットして返す"""
        if not self.alerts:
            return "  アラート: 設定されていません"

        lines = [
            "=" * 50,
            "  アラート一覧",
            "=" * 50,
        ]
        for i, alert in enumerate(self.alerts):
            direction = "以上" if alert["direction"] == "above" else "以下"
            lines.append(f"  [{i}] ¥{alert['price']:,.0f} {direction}")
        lines.append("=" * 50)
        return "\n".join(lines)

    def notify_windows(self, alert, current_price):
        """Windows通知を送信する"""
        try:
            from subprocess import Popen
            direction = "到達" if alert["direction"] == "above" else "下落"
            title = "ETH 価格アラート"
            msg = f"ETH価格が¥{alert['price']:,.0f}{direction}しました（現在: ¥{current_price:,.0f}）"
            # PowerShellでトースト通知
            ps_cmd = (
                f"[Windows.UI.Notifications.ToastNotificationManager, "
                f"Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
                f"$template = [Windows.UI.Notifications.ToastNotificationManager]"
                f"::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]"
                f"::ToastText02); "
                f"$text = $template.GetElementsByTagName('text'); "
                f"$text.Item(0).AppendChild($template.CreateTextNode('{title}')); "
                f"$text.Item(1).AppendChild($template.CreateTextNode('{msg}')); "
                f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
                f"[Windows.UI.Notifications.ToastNotificationManager]"
                f"::CreateToastNotifier('ETH Terminal').Show($toast)"
            )
            Popen(
                ["powershell", "-Command", ps_cmd],
                creationflags=0x08000000
            )
        except Exception:
            print(f"  [アラート] ¥{alert['price']:,.0f} に到達（¥{current_price:,.0f}）")

    def start_monitor(self, price_func, interval=10):
        """バックグラウンドで価格監視を開始する"""
        if self._running:
            return

        self._running = True

        def _monitor():
            while self._running:
                try:
                    prices = price_func()
                    if prices:
                        current = prices["eth_jpy"]
                        triggered = self.check_alerts(current)
                        for alert in triggered:
                            self.notify_windows(alert, current)
                except Exception:
                    pass
                time.sleep(interval)

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self._monitor_thread.start()

    def stop_monitor(self):
        """価格監視を停止する"""
        self._running = False
