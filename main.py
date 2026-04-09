import json
import requests

from config import DAYS_TO_KEEP
from logger import logger
from services.supabase_service import load_posted, cleanup_old_links
from rss.feed_processor import process_feed


def main():
    logger.info("Starting RSS Bot")

    cleanup_old_links(DAYS_TO_KEEP)
    posted_links = load_posted(DAYS_TO_KEEP)

    try:
        with open("data/feeds.json", "r", encoding="utf-8") as f:
            feeds = json.load(f).get("feeds", [])

        if not feeds:
            logger.error("No feeds found")
            return

        with requests.Session() as session:
            for feed in feeds:
                process_feed(session, feed, posted_links)

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()