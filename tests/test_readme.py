"""説明書モジュールのテスト"""
from unittest.mock import MagicMock
from rich.console import Console
from src.readme import build_readme, SECTIONS


class TestSections:
    def test_sections_is_dict(self):
        assert isinstance(SECTIONS, dict)

    def test_has_overview_section(self):
        assert "overview" in SECTIONS

    def test_has_price_section(self):
        assert "price" in SECTIONS

    def test_has_chart_section(self):
        assert "chart" in SECTIONS

    def test_has_indicators_section(self):
        assert "indicators" in SECTIONS

    def test_has_alert_section(self):
        assert "alert" in SECTIONS

    def test_has_position_section(self):
        assert "position" in SECTIONS

    def test_has_news_section(self):
        assert "news" in SECTIONS

    def test_has_ask_section(self):
        assert "ask" in SECTIONS


class TestBuildReadme:
    def test_full_readme_is_renderable(self):
        result = build_readme()
        console = Console(file=MagicMock(), width=100)
        console.print(result)

    def test_section_readme_is_renderable(self):
        result = build_readme("price")
        console = Console(file=MagicMock(), width=100)
        console.print(result)

    def test_unknown_section_returns_error(self):
        result = build_readme("nonexistent")
        console = Console(file=MagicMock(), width=100)
        console.print(result)
