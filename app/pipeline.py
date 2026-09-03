import logging

from app.ai.client import OpenRouterClient
from app.ai.classifier import analyze_article
from app.collectors.article import ArticleExtractor
from app.collectors.rss import RSSCollector
from app.config import settings
from app.database import D1Database
from app.telegram.publisher import TelegramPublisher

log = logging.getLogger(__name__)

class NewsPipeline:
    def __init__(self, db, telegram: TelegramPublisher):
        self.db = db
        self.telegram = telegram

        self.rss = RSSCollector(settings.sources_path)

        self.extractor = ArticleExtractor(
            timeout=settings.request_timeout_seconds,
            max_chars=settings.max_article_chars,
            user_agent=settings.user_agent,
        )

        self.ai = OpenRouterClient(
            settings.openrouter_api_key,
            settings.openrouter_model,
        )

    async def run_cycle(self):
        await self.db.initialize()

        candidates = await self.rss.collect()

        log.info("Collected %d candidates", len(candidates))

        unique = []
        seen_urls = set()
        seen_hashes = set()

        for article in candidates:
            if article.url in seen_urls:
                continue

            title_hash = D1Database.title_hash(article.title)
            if title_hash in seen_hashes:
                continue

            seen_urls.add(article.url)
            seen_hashes.add(title_hash)

            if await self.db.exists(article.url, article.title):
                continue

            unique.append(article)

            if len(unique) >= settings.max_articles_per_cycle:
                break

        log.info("New candidates: %d", len(unique))

        published_count = 0

        for article in unique:
            try:
                await self.db.insert_article(article)

                article.content = await self.extractor.extract(article.url)

                analysis = await analyze_article(self.ai, article)

                await self.db.save_analysis(article.url, analysis)

                log.info(
                    "Analyzed | AI=%s interesting=%s score=%d | %s",
                    analysis.is_ai_news,
                    analysis.interesting,
                    analysis.score,
                    article.title,
                )

                if (
                    analysis.is_ai_news
                    and analysis.interesting
                    and analysis.score >= settings.min_ai_score
                ):
                    message_id = await self.telegram.publish(
                        headline=analysis.headline,
                        summary=analysis.summary,
                        why_it_matters=analysis.why_it_matters,
                        category=analysis.category,
                        source_url=article.url,
                        urgent=analysis.score > 80,
                    )

                    await self.db.mark_posted(
                        article.url,
                        message_id,
                    )

                    published_count += 1

                    log.info("Published: %s", analysis.headline)

            except Exception:
                # One broken article/provider response must not stop
                # the remaining candidates.
                log.exception("Failed article: %s", article.url)

        log.info(
            "Cycle complete | published %d / analyzed %d / candidates %d",
            published_count,
            len(unique),
            len(candidates),
        )
