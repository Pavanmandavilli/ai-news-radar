import asyncio

from app.collectors.rss import RSSCollector
from app.config import settings

async def main():
    rss = RSSCollector(settings.sources_path)

    a = await rss.collect()

    print("RSS:", len(a))
    for item in a[:10]:
        print(item.title, item.url)

if __name__ == "__main__":
    asyncio.run(main())
