import html
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Set

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import Client, create_client

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# load environment variables
load_dotenv()

# constants
TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")
MAX_ITEMS_PER_FEED = 20
DAYS_TO_KEEP = 3


if not TOKEN:
    logger.error("TELEGRAM_TOKEN not found in environment variables")
    raise ValueError("TELEGRAM_TOKEN is required")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found.")
    raise ValueError("SUPABASE_URL and SUPABASE_KEY are required.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Error connecting to Supabase: {e}")
    raise


def load_posted(days: int = DAYS_TO_KEEP) -> Set[str]:
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        response = (
            supabase.table("posted_links")
            .select("link")
            .gte("posted_at", cutoff_date)
            .execute()
        )

        if hasattr(response, "data") and response.data:
            links = {item["link"] for item in response.data}
            logger.info(f"{len(links)} links recentes carregados do Supabase")
            return links

        logger.info("Nenhum link recente encontrado no Supabase.")
        return set()
    except Exception as e:
        logger.error(f"Erro ao carregar links do Supabase: {e}")
        return set()


def save_posted(link: str, feed_name: str, title: str = "") -> bool:
    try:
        data = {
            "link": link,
            "feed_name": feed_name,
            "title": title[:255] if title else "",
            "posted_at": datetime.now().isoformat(),
        }

        response = supabase.table("posted_links").insert(data).execute()

        if hasattr(response, "data") and response.data:
            logger.debug(f"Link saved: {link[:50]}...")
            return True
        else:
            logger.warning(f"Unexpected response when saving: {response}")
            return False
    except Exception as e:
        if "duplicate key" in str(e).lower():
            logger.debug(f"Link already exists (duplicate ignored): {link[:50]}...")
            return True
        else:
            logger.error(f"Error saving link in Supabase: {e}")
            return False


def cleanup_old_links(days: int) -> None:
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        supabase.table("posted_links").delete().lt("posted_at", cutoff).execute()
        logger.info(f"Cleanup completed ({days} days)")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def clean_summary(summary: str, max_length: int = 300) -> str:
    if not summary:
        return ""

    try:
        soup = BeautifulSoup(summary, "html.parser")
        text = soup.get_text()
        text = " ".join(text.split())

        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."

        return html.escape(text)

    except Exception:
        return html.escape(summary[:max_length])


def send_message(session: requests.Session, message: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    for attempt in range(3):
        try:
            r = session.post(url, data=payload, timeout=10)

            if r.status_code == 200:
                return True

            logger.warning(f"Error {r.status_code}: {r.text}")

        except requests.RequestException as e:
            logger.warning(f"Connection Error: {e}")

        time.sleep(2**attempt)

    return False


def process_feed(
    session: requests.Session, feed_info: Dict[str, str], posted_links: Set[str]
) -> None:
    feed_name = feed_info.get("name", "Unknown feed")
    feed_url = feed_info.get("url", "")

    if not feed_url:
        logger.error(f"Feed {feed_name} has no defined URL.")
        return

    logger.info(f"Processing feed: {feed_name}")

    try:
        feed = feedparser.parse(
            feed_url,
            request_headers={"User-Agent": "Mozilla/5.0"},
        )
        if hasattr(feed, "bozo") and feed.bozo:
            logger.warning(
                f"Feed {feed_name} may have parsing issues: {feed.bozo_exception}"
            )

        if not feed.entries:
            logger.warning(f"Feed {feed_name} did not return any entries.")
            return

        new_news = 0

        for i, entry in enumerate(feed.entries[:MAX_ITEMS_PER_FEED]):
            try:
                link = entry.get("link", "")
                if not link:
                    logger.warning(f"Entry {i} from feed {feed_name} has no link.")
                    continue
                if link in posted_links:
                    logger.debug(f"Link already posted: {link[:50]}...")
                    continue

                title = entry.get("title", "No title")

                summary = entry.get("summary", "")
                if not summary and "content" in entry:
                    summary = entry.content[0].value

                clean_text = clean_summary(summary)

                message = (
                    f"📰 <b>{feed_name}</b>\n\n"
                    f"<b>{title}</b>\n\n"
                    f"{clean_text}\n\n"
                    f"🔗 <a href='{link}'>Leia mais</a>"
                )

                success = False
                success = send_message(session, CHANNEL, message)

                if success:
                    if save_posted(link, feed_name, title):
                        posted_links.add(link)
                        new_news += 1
                        logger.info(f"News published: {title[:50]}...")
                    else:
                        logger.error(f"News sent but link not saved: {title[:50]}...")
                else:
                    logger.error(f"Failed to publish news: {title[:50]}...")

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing entry {i} from feed {feed_name}: {e}")
                continue

        logger.info(f"{feed_name}: {new_news} new news.")
    except Exception as e:
        logger.error(f"Error processing feed {feed_name}: {e}")


def main():
    logger.info("=" * 50)
    logger.info("Starting RSS Bot for Telegram")
    logger.info("=" * 50)

    cleanup_old_links(days=DAYS_TO_KEEP)
    posted_links = load_posted(days=DAYS_TO_KEEP)

    try:
        with open("feeds.json", "r", encoding="utf-8") as f:
            feeds_data = json.load(f)
            feeds = feeds_data.get("feeds", [])

        if not feeds:
            logger.error("No feeds found in the feeds.json file.")
            return

        logger.info(f"Loaded {len(feeds)} feeds to monitor")

        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=5) as executor:
                for feed in feeds:
                    logger.info(f"  - {feed.get('name')}: {feed.get('url')}")
                    executor.submit(process_feed, session, feed, posted_links)
    except FileNotFoundError:
        logger.error("Feeds.json file not found.")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing feeds.json: {e}")
        return
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main cycle: {e}")
        logger.info("Trying to continue...")


if __name__ == "__main__":
    main()
