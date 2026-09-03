# AI News Telegram Bot — GitHub Actions Production

A personal, low-cost AI-news publishing bot designed to run as a **one-shot GitHub Actions job** every 15 minutes.

## Architecture

GitHub Actions (public repository)
        |
        v
Python one-shot worker
        |
        +--> GDELT
        +--> RSS feeds
        |
        v
Cloudflare D1 (persistent duplicate/history database)
        |
        v
OpenRouter via OpenAI Python SDK
        |
        v
AI relevance + editorial filtering
        |
        v
Telegram Bot API
        |
        v
Your Telegram channel
        |
        +--> "Read Original Article" button

The internal AI score is NEVER shown in Telegram.

## Cost model

- GitHub Actions: standard GitHub-hosted runners are free for public repositories.
- Cloudflare D1: Free plan currently includes 5 million rows read/day, 100,000 rows written/day and 5 GB total storage.
- Telegram Bot API: no paid bot hosting is required.
- GDELT/RSS: public sources.
- OpenRouter: depends on the model you select. Use a currently available free model if you want the LLM part to remain free.

Free service limits can change. Check the provider's current documentation before deployment.

## Requirements

1. A PUBLIC GitHub repository.
2. A GitHub account with Actions enabled.
3. A Cloudflare account.
4. A Cloudflare D1 database.
5. A Cloudflare API token with permission to query the D1 database.
6. An OpenRouter API key.
7. A Telegram bot token.
8. A Telegram channel where the bot is an administrator.

## 1. Create a Cloudflare D1 database

Create a D1 database in the Cloudflare dashboard.

Then create the table using the SQL in:

    database/schema.sql

You will need these values:

    CLOUDFLARE_ACCOUNT_ID
    CLOUDFLARE_D1_DATABASE_ID

Do NOT put these values directly into the Python code.

## 2. Create a Cloudflare API token

Create a token that has the minimum D1 permissions needed to query the database.

For this application, the token is used only by the GitHub Actions job to execute SQL against D1.

Store the token as a GitHub Actions secret:

    CLOUDFLARE_API_TOKEN

Keep the token secret even though the repository is public.

## 3. GitHub Actions secrets

Open:

    Repository -> Settings -> Secrets and variables -> Actions

Create these repository secrets:

    OPENROUTER_API_KEY
    OPENROUTER_MODEL
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHANNEL_ID
    CLOUDFLARE_API_TOKEN
    CLOUDFLARE_ACCOUNT_ID
    CLOUDFLARE_D1_DATABASE_ID

Example values:

    OPENROUTER_MODEL=your-current-openrouter-model-id
    TELEGRAM_CHANNEL_ID=@your_channel

Do not commit .env or API keys.

## 4. Telegram

1. Create a bot with BotFather.
2. Add the bot as an administrator of your channel.
3. Give it permission to post messages.
4. Put the bot token in GitHub Actions secrets.
5. Use @yourchannelusername as TELEGRAM_CHANNEL_ID if the channel is public.

## 5. Enable the workflow

The workflow is:

    .github/workflows/news.yml

It runs every 15 minutes and can also be started manually from the GitHub Actions tab.

GitHub scheduled workflows use UTC unless a timezone is explicitly configured. The workflow in this project uses UTC and runs at 5, 20, 35 and 50 minutes past each hour.

## 6. First test

Before enabling real Telegram posting, edit the workflow or repository variable so:

    DRY_RUN=true

The workflow will analyze and print what it would publish without sending to Telegram.

Once the output looks correct, change it to:

    DRY_RUN=false

This value is configured in the workflow's env section, not as a repository secret.

## 7. How duplicate detection works

D1 stores:

- article URL
- normalized title hash
- source
- publication/discovery time
- AI analysis
- whether it was posted
- Telegram message ID

A new run checks D1 before analyzing an article.

This prevents the same URL/title from being sent repeatedly.

## 8. Important limitation

This does not guarantee discovery of every article on the internet.

It combines GDELT and RSS feeds. More RSS/official sources can be added in:

    config/sources.json

For stronger coverage, add feeds from the AI companies and publications you care about.

## 9. Production behavior

The Python process runs ONE cycle and exits.

GitHub Actions is the scheduler.

Do not add an infinite while/sleep loop to main.py.

That gives:

    00:05 -> one run
    00:20 -> one run
    00:35 -> one run
    00:50 -> one run

If one run fails, the next scheduled run can recover.

## 10. Local testing

Create a local .env using .env.example.

Then:

    pip install -r requirements.txt
    python main.py

Set:

    DRY_RUN=true

for safe local testing.

## 11. Adding RSS feeds

Edit:

    config/sources.json

Example:

    {
      "name": "Example AI",
      "url": "https://example.com/feed/"
    }

Only add feeds you are permitted to access.

## 12. Security

Never commit:

- OpenRouter keys
- Telegram bot tokens
- Cloudflare API tokens
- Cloudflare account secrets

The repository is intentionally public, so all secrets must be stored in GitHub Actions Secrets.

## 13. Recommended next upgrades

After V1 is stable:

- semantic duplicate detection
- source reliability weighting
- breaking-news priority
- retry/backoff per provider
- per-source rate limiting
- better article freshness detection
- optional admin Telegram commands
- daily digest mode
