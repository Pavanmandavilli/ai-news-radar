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

CREATE INDEX IF NOT EXISTS idx_articles_url
ON articles(url);

CREATE INDEX IF NOT EXISTS idx_articles_hash
ON articles(normalized_hash);

CREATE INDEX IF NOT EXISTS idx_articles_posted
ON articles(posted);

CREATE INDEX IF NOT EXISTS idx_articles_discovered
ON articles(discovered_at);
