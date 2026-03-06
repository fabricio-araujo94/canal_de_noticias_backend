import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

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
CHANNEL = "@jornaldepedra"
MAX_ITEMS_PER_FEED = 5

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


def load_posted() -> Set[str]:
    try:
        response = supabase.table("posted_links").select("link").execute()

        if hasattr(response, "data") and response.data:
            links = {item["link"] for item in response.data}
            logger.info(f"{len(links)} links from Supabase loaded")
            return links

        logger.info("No links found in Supabase.")
        return set()
    except Exception as e:
        logger.error(f"Error loading links from Supabase: {e}")
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


def cleanup_old_links(days: int = 30) -> int:
    try:
        cutoff_date = datetime.now() - timedelta(days=days).isoformat()

        response = (
            supabase.table("posted_links")
            .delete()
            .lt("posted_at", cutoff_date)
            .execute()
        )

        if hasattr(response, "data") and response.data:
            count = len(response.data)
            logger.info(f"Removed {count} links older than {days} days.")
            return count

        return 0
    except Exception as e:
        logger.error(f"Error while clearing old links: {e}")
        return 0


def clean_summary(summary: str, max_length: int = 300) -> str:
    try:
        if not summary:
            return ""

        soup = BeautifulSoup(summary, "html.parser")
        text = soup.get_text()
        text = " ".join(text.split())

        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."
        return text
    except Exception as e:
        logger.warning(f"Error while clearing summary: {e}")
        return summary[:max_length] + "..." if summary else ""


def send_message(channel: str, message: str, retry: int = 3) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    for attempt in range(retry):
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Message sent successfully.")
                return True
            else:
                logger.warning(
                    f"Attempt {attempt + 1}: Error sending message. Status: {response.status_code}"
                )
                if attempt < retry - 1:
                    time.sleep(2**attempt)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}: Connection error: {e}")
            if attempt < retry - 1:
                time.sleep(2**attempt)

    logger.error(f"Failed to send message after {retry} attempts.")
    return False


def process_feed(feed_info: Dict[str, str], posted_links: Set[str]) -> None:
    feed_name = feed_info.get("name", "Unknown feed")
    feed_url = feed_info.get("url", "")

    if not feed_url:
        logger.error(f"Feed {feed_name} has no defined URL.")
        return

    logger.info(f"Processing feed: {feed_name}")

    try:
        feed = feedparser.parse(feed_url)
        if hasattr(feed, "bozo") and feed.bozo:
            logger.warning(
                f"Feed {feed_name} may have parsing issues: {feed.bozo_exception}"
            )

        if not feed.entries:
            logger.warning(f"“Feed {feed_name} did not return any entries.”")
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

                clean_text = clean_summary(summary)

                message = (
                    f"📰 <b>{feed_name}</b>\n\n"
                    f"<b>{title}</b>\n\n"
                    f"{clean_text}\n\n"
                    f"🔗 <a href='{link}'>Leia mais</a>"
                )

                success = False
                success = send_message(CHANNEL, message)

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

    posted_links = load_posted()

    cleanup_old_links(days=30)

    try:
        with open("feeds.json", "r", encoding="utf-8") as f:
            feeds_data = json.load(f)
            feeds = feeds_data.get("feeds", [])

        if not feeds:
            logger.error("No feeds found in the feeds.json file.")
            return

        logger.info(f"Loaded {len(feeds)} feeds to monitor")
        for feed in feeds:
            logger.info(f"  - {feed.get('name')}: {feed.get('url')}")
            process_feed(feed, posted_links)
            time.sleep(5)
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
