import json
import logging
import re

from app.ai.client import OpenRouterClient
from app.models import Article, AIAnalysis

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are the editorial classifier for a Telegram channel dedicated ONLY to
important and interesting artificial-intelligence news.

Prefer:
- major AI model releases or upgrades
- important AI research
- major AI company announcements
- significant AI funding, acquisitions, partnerships and contracts
- significant AI revenue/profit/business results
- AI chips and infrastructure
- important AI agents, robotics and products
- major AI regulation, lawsuits or policy developments

Reject:
- generic SEO content
- listicles
- trivial AI feature updates
- articles that only mention AI
- promotional spam
- old stories without meaningful new developments
- low-importance rumors

Return ONLY valid JSON:

{
  "is_ai_news": true,
  "interesting": true,
  "score": 0,
  "category": "AI Models",
  "headline": "Concise factual headline",
  "summary": "2-3 sentence original summary",
  "why_it_matters": "One short sentence explaining significance"
}

The score is INTERNAL ONLY and must never appear in the generated post.
Do not invent facts.
Do not claim information that is not supported by the article.
"""

def extract_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("LLM response did not contain JSON")

    return json.loads(match.group(0))

async def analyze_article(client: OpenRouterClient, article: Article):
    body = article.content or article.description or "(No article body available.)"

    user = f"""
TITLE:
{article.title}

SOURCE:
{article.source}

PUBLISHED:
{article.published_at or "unknown"}

URL:
{article.url}

ARTICLE:
{body}
"""

    raw = await client.complete(SYSTEM_PROMPT, user)
    data = extract_json(raw)

    score = max(0, min(100, int(data.get("score", 0))))

    return AIAnalysis(
        is_ai_news=bool(data.get("is_ai_news", False)),
        interesting=bool(data.get("interesting", False)),
        score=score,
        category=str(data.get("category", "AI News")).strip() or "AI News",
        headline=str(data.get("headline", article.title)).strip() or article.title,
        summary=str(data.get("summary", "")).strip(),
        why_it_matters=str(data.get("why_it_matters", "")).strip(),
    )
