import logging

import httpx
import trafilatura

log = logging.getLogger(__name__)

class ArticleExtractor:
    def __init__(self, timeout=20, max_chars=12000, user_agent="AI-News-Radar/1.0"):
        self.timeout = timeout
        self.max_chars = max_chars
        self.user_agent = user_agent

    async def extract(self, url):
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            text = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
            )
            return (text or "")[:self.max_chars]
        except Exception:
            log.warning("Article extraction failed: %s", url)
            return ""
