"""ニュース取得モジュールのテスト"""
from unittest.mock import patch, MagicMock
from src.news import fetch_news, filter_iran_news, format_news_display


def _make_entry(title, link, published, summary):
    """テスト用エントリを作成"""
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.published = published
    entry.summary = summary
    return entry


def _mock_entries():
    return [
        _make_entry(
            "Bitcoin hits new high", "https://example.com/1",
            "2024-01-01", "BTC surges past $100k"),
        _make_entry(
            "Iran sanctions impact crypto markets", "https://example.com/2",
            "2024-01-02", "Iran-related sanctions affect trading"),
        _make_entry(
            "Ethereum upgrade announced", "https://example.com/3",
            "2024-01-03", "ETH network upgrade"),
    ]


class TestFetchNews:
    def test_returns_entries(self):
        feed = MagicMock()
        feed.entries = _mock_entries()
        with patch("src.news.feedparser.parse", return_value=feed):
            entries = fetch_news(feeds=["https://example.com/rss"], limit=3)
        assert len(entries) == 3

    def test_respects_limit(self):
        feed = MagicMock()
        feed.entries = _mock_entries()
        with patch("src.news.feedparser.parse", return_value=feed):
            entries = fetch_news(feeds=["https://example.com/rss"], limit=1)
        assert len(entries) == 1


class TestFilterIranNews:
    def test_filters_iran_related(self):
        entries = _mock_entries()
        filtered = filter_iran_news(entries)
        assert len(filtered) == 1
        assert "iran" in filtered[0].title.lower()

    def test_returns_empty_when_no_match(self):
        entries = [
            _make_entry(
                "Bitcoin news", "https://example.com/1",
                "2024-01-01", "No related content"),
        ]
        filtered = filter_iran_news(entries)
        assert len(filtered) == 0


class TestFormatNewsDisplay:
    def test_formats_correctly(self):
        entries = _mock_entries()
        output = format_news_display(entries)
        assert "Bitcoin" in output
        assert "Ethereum" in output

    def test_format_empty(self):
        output = format_news_display([])
        assert "なし" in output or "ニュース" in output
