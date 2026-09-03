import asyncio
import logging
import os

from app.config import settings, validate_settings
from app.database import D1Database
from app.pipeline import NewsPipeline
from app.telegram.publisher import TelegramPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

async def main():
    validate_settings()

    db = D1Database(
        api_token=settings.cloudflare_api_token,
        account_id=settings.cloudflare_account_id,
        database_id=settings.cloudflare_d1_database_id,
        timeout=settings.request_timeout_seconds,
    )

    telegram = TelegramPublisher(
        bot_token=settings.telegram_bot_token,
        channel_id=settings.telegram_channel_id,
        timeout=settings.request_timeout_seconds,
        dry_run=settings.dry_run,
    )

    pipeline = NewsPipeline(db=db, telegram=telegram)
    await pipeline.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
