import html
import time
import feedparser
from threading import Lock
from typing import Dict, Set

from config import CHANNEL, MAX_ITEMS_PER_FEED
from logger import logger
from services.telegram_service import send_message
from services.supabase_service import save_posted
from utils.text import clean_summary
from utils.date import is_recent

lock = Lock()


def process_feed(session, feed_info: Dict, posted_links: Set[str]):
    name = feed_info.get("name", "Unknown")
    url = feed_info.get("url")

    if not url:
        logger.error(f"{name} has no URL")
        return

    logger.info(f"[{name}] Processing")

    feed = feedparser.parse(url)

    if not feed.entries:
        logger.warning(f"[{name}] No entries")
        return

    for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
        link = entry.get("link")

        if not link:
            continue

        with lock:
            if link in posted_links:
                continue

        if not is_recent(entry):
            continue

        title_raw = entry.get("title", "No title")
        title = html.escape(title_raw)

        summary = entry.get("summary", "")
        clean_text = clean_summary(summary)

        message = (
            f"📰 <b>{html.escape(name)}</b>\n\n"
            f"<b>{title}</b>\n\n"
            f"{clean_text}\n\n"
            f"🔗 <a href='{link}'>Read more</a>"
        )

        if send_message(session, CHANNEL, message):
            if save_posted(link, name, title_raw):
                with lock:
                    posted_links.add(link)

        time.sleep(2)