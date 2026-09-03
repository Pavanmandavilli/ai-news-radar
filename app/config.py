import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def _int(name, default):
    return int(os.getenv(name, str(default)))

def _bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_channel_id: str = os.getenv("TELEGRAM_CHANNEL_ID", "")

    cloudflare_api_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_account_id: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cloudflare_d1_database_id: str = os.getenv("CLOUDFLARE_D1_DATABASE_ID", "")

    dry_run: bool = _bool("DRY_RUN", True)
    min_ai_score: int = _int("MIN_AI_SCORE", 70)
    max_articles_per_cycle: int = _int("MAX_ARTICLES_PER_CYCLE", 30)
    request_timeout_seconds: int = _int("REQUEST_TIMEOUT_SECONDS", 20)
    max_article_chars: int = _int("MAX_ARTICLE_CHARS", 12000)
    user_agent: str = os.getenv("USER_AGENT", "AI-News-Radar/1.0")

    sources_path: str = str(BASE_DIR / "config" / "sources.json")

settings = Settings()

def validate_settings():
    required = [
        ("OPENROUTER_API_KEY", settings.openrouter_api_key),
        ("OPENROUTER_MODEL", settings.openrouter_model),
        ("CLOUDFLARE_API_TOKEN", settings.cloudflare_api_token),
        ("CLOUDFLARE_ACCOUNT_ID", settings.cloudflare_account_id),
        ("CLOUDFLARE_D1_DATABASE_ID", settings.cloudflare_d1_database_id),
    ]

    if not settings.dry_run:
        required += [
            ("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token),
            ("TELEGRAM_CHANNEL_ID", settings.telegram_channel_id),
        ]

    missing = [name for name, value in required if not value]
    if missing:
        raise RuntimeError("Missing configuration: " + ", ".join(missing))
