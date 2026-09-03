import html
import logging

import httpx

log = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self, bot_token, channel_id, timeout=20, dry_run=True):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.timeout = timeout
        self.dry_run = dry_run

    @property
    def api_url(self):
        return f"https://api.telegram.org/bot{self.bot_token}"

    @staticmethod
    def format_message(headline, summary, why_it_matters, category, urgent=False):
        icon = "🚨" if urgent else "📰"
        return (
            f"<b>{icon} {html.escape(headline)}</b>\n\n"
            f"{html.escape(summary)}\n\n"
            f"<b>💡 Why it matters:</b>\n"
            f"{html.escape(why_it_matters)}\n\n"
            f"<b>🏷 {html.escape(category)}</b>"
        )

    async def publish(
        self,
        headline,
        summary,
        why_it_matters,
        category,
        source_url,
        urgent=False,
    ):
        message = self.format_message(
            headline,
            summary,
            why_it_matters,
            category,
            urgent=urgent,
        )

        if self.dry_run:
            log.info(
                "\n--- DRY RUN ---\n%s\nSOURCE: %s\n--------------",
                message,
                source_url,
            )
            return "dry-run"

        payload = {
            "chat_id": self.channel_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [{
                        "text": "🔗 Read Original Article",
                        "url": source_url,
                    }]
                ]
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/sendMessage",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")

        return str(data["result"]["message_id"])
