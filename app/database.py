import hashlib
import re

import httpx

class D1Database:

    def __init__(self, api_token, account_id, database_id, timeout=20):
        self.api_token = api_token
        self.account_id = account_id
        self.database_id = database_id
        self.timeout = timeout
        self.endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{account_id}/d1/database/{database_id}/query"
        )

    async def execute(self, sql, params=None):
        payload = {
            "sql": sql,
            "params": params or [],
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers,
        ) as client:
            response = await client.post(self.endpoint, json=payload)

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"D1 API error: {data}")

        return data.get("result", [])

    @staticmethod
    def normalize_title(title: str) -> str:
        title = title.lower()
        title = re.sub(r"https?://\S+", "", title)
        title = re.sub(r"[^a-z0-9\s]", " ", title)
        title = re.sub(r"\s+", " ", title).strip()
        return title

    @classmethod
    def title_hash(cls, title: str) -> str:
        return hashlib.sha256(
            cls.normalize_title(title).encode("utf-8")
        ).hexdigest()

    async def initialize(self):
        schema = """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            normalized_hash TEXT NOT NULL UNIQUE,
            source TEXT,
            published_at TEXT,
            discovered_at TEXT NOT NULL,
            is_ai_news INTEGER,
            interesting INTEGER,
            score INTEGER,
            category TEXT,
            generated_headline TEXT,
            summary TEXT,
            why_it_matters TEXT,
            posted INTEGER NOT NULL DEFAULT 0,
            telegram_message_id TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
        CREATE INDEX IF NOT EXISTS idx_articles_hash ON articles(normalized_hash);
        CREATE INDEX IF NOT EXISTS idx_articles_posted ON articles(posted);
        CREATE INDEX IF NOT EXISTS idx_articles_discovered ON articles(discovered_at);
        """
        # D1 accepts multiple statements in a query in normal SQLite syntax
        # through the API. If your account/API rejects a multi-statement
        # request, run database/schema.sql once in the D1 dashboard instead.
        await self.execute(schema)

    async def exists(self, url, title):
        h = self.title_hash(title)
        result = await self.execute(
            """
            SELECT id FROM articles
            WHERE url = ? OR normalized_hash = ?
            LIMIT 1
            """,
            [url, h],
        )
        return bool(result and result[0].get("results"))

    async def insert_article(self, article):
        from datetime import datetime, timezone

        h = self.title_hash(article.title)
        now = datetime.now(timezone.utc).isoformat()

        result = await self.execute(
            """
            INSERT OR IGNORE INTO articles
            (url, title, normalized_hash, source, published_at,
             discovered_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                article.url,
                article.title,
                h,
                article.source,
                article.published_at,
                article.discovered_at,
                now,
            ],
        )

        return True

    async def save_analysis(self, url, analysis):
        await self.execute(
            """
            UPDATE articles
            SET is_ai_news = ?,
                interesting = ?,
                score = ?,
                category = ?,
                generated_headline = ?,
                summary = ?,
                why_it_matters = ?
            WHERE url = ?
            """,
            [
                int(analysis.is_ai_news),
                int(analysis.interesting),
                analysis.score,
                analysis.category,
                analysis.headline,
                analysis.summary,
                analysis.why_it_matters,
                url,
            ],
        )

    async def mark_posted(self, url, telegram_message_id):
        await self.execute(
            """
            UPDATE articles
            SET posted = 1, telegram_message_id = ?
            WHERE url = ?
            """,
            [telegram_message_id, url],
        )
