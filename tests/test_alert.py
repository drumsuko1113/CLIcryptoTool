"""アラートモジュールのテスト"""
from src.alert import AlertManager


class TestAlertManager:
    def setup_method(self):
        self.manager = AlertManager()

    def test_add_alert(self):
        self.manager.add_alert(350000, "above")
        assert len(self.manager.alerts) == 1
        assert self.manager.alerts[0]["price"] == 350000
        assert self.manager.alerts[0]["direction"] == "above"

    def test_add_multiple_alerts(self):
        self.manager.add_alert(350000, "above")
        self.manager.add_alert(300000, "below")
        assert len(self.manager.alerts) == 2

    def test_remove_alert(self):
        self.manager.add_alert(350000, "above")
        self.manager.add_alert(300000, "below")
        self.manager.remove_alert(0)
        assert len(self.manager.alerts) == 1
        assert self.manager.alerts[0]["price"] == 300000

    def test_remove_alert_invalid_index(self):
        self.manager.add_alert(350000, "above")
        result = self.manager.remove_alert(5)
        assert result is False
        assert len(self.manager.alerts) == 1

    def test_check_alerts_triggered_above(self):
        self.manager.add_alert(350000, "above")
        triggered = self.manager.check_alerts(360000)
        assert len(triggered) == 1
        assert triggered[0]["price"] == 350000

    def test_check_alerts_not_triggered(self):
        self.manager.add_alert(350000, "above")
        triggered = self.manager.check_alerts(340000)
        assert len(triggered) == 0

    def test_check_alerts_triggered_below(self):
        self.manager.add_alert(300000, "below")
        triggered = self.manager.check_alerts(290000)
        assert len(triggered) == 1

    def test_triggered_alerts_are_removed(self):
        self.manager.add_alert(350000, "above")
        self.manager.check_alerts(360000)
        assert len(self.manager.alerts) == 0

    def test_format_alerts_list(self):
        self.manager.add_alert(350000, "above")
        self.manager.add_alert(300000, "below")
        output = self.manager.format_alerts()
        assert "350,000" in output
        assert "300,000" in output

    def test_format_empty_alerts(self):
        output = self.manager.format_alerts()
        assert "なし" in output or "設定されていません" in output
