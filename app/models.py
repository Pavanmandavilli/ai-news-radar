from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Article:
    title: str
    url: str
    source: str
    published_at: str | None = None
    description: str = ""
    content: str = ""
    discovered_at: str = ""

    def __post_init__(self):
        if not self.discovered_at:
            self.discovered_at = datetime.now(timezone.utc).isoformat()

@dataclass
class AIAnalysis:
    is_ai_news: bool
    interesting: bool
    score: int
    category: str
    headline: str
    summary: str
    why_it_matters: str
