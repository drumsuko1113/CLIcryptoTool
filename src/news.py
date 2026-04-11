"""ニュース取得モジュール（RSS使用）"""
import feedparser

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]

IRAN_KEYWORDS = [
    "iran", "イラン", "tehran", "テヘラン",
    "persian", "khamenei", "ハメネイ",
    "sanctions", "制裁",
]


def fetch_news(feeds=None, limit=10):
    """RSSフィードからニュースを取得する"""
    if feeds is None:
        feeds = RSS_FEEDS

    all_entries = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            all_entries.extend(feed.entries)
        except Exception:
            continue

    all_entries.sort(
        key=lambda e: getattr(e, "published", ""),
        reverse=True
    )
    return all_entries[:limit]


def filter_iran_news(entries):
    """イラン関連ニュースをフィルタする"""
    filtered = []
    for entry in entries:
        text = (
            getattr(entry, "title", "") + " " +
            getattr(entry, "summary", "")
        ).lower()
        if any(kw in text for kw in IRAN_KEYWORDS):
            filtered.append(entry)
    return filtered


def format_news_display(entries, title="ニュース"):
    """ニュースエントリをフォーマットして返す"""
    lines = [
        "=" * 60,
        f"  {title}",
        "=" * 60,
    ]

    if not entries:
        lines.append("  ニュースはありません")
    else:
        for i, entry in enumerate(entries):
            pub = getattr(entry, "published", "不明")
            lines.append(f"  [{i+1}] {entry.title}")
            lines.append(f"      {pub}")
            lines.append(f"      {entry.link}")
            lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
