import itertools
import json
import logging
from pathlib import Path

import feedparser

from app.models import Article

log = logging.getLogger(__name__)

class RSSCollector:
    def __init__(self, sources_path):
        self.sources_path = Path(sources_path)

    def feeds(self):
        data = json.loads(self.sources_path.read_text(encoding="utf-8"))
        return data.get("rss_feeds", [])

    async def collect(self, max_per_feed=20):
        per_feed_articles = []

        for cfg in self.feeds():
            feed_articles = []
            try:
                feed = feedparser.parse(cfg["url"])
                for entry in feed.entries[:max_per_feed]:
                    url = entry.get("link", "").strip()
                    title = entry.get("title", "").strip()
                    if not url or not title:
                        continue

                    feed_articles.append(Article(
                        title=title,
                        url=url,
                        source=cfg["name"],
                        published_at=(
                            entry.get("published")
                            or entry.get("updated")
                            or None
                        ),
                        description=(
                            entry.get("summary")
                            or entry.get("description")
                            or ""
                        ),
                    ))
            except Exception:
                log.exception("RSS failed: %s", cfg["url"])

            per_feed_articles.append(feed_articles)

        articles = []
        for row in itertools.zip_longest(*per_feed_articles):
            for article in row:
                if article is not None:
                    articles.append(article)

        return articles
