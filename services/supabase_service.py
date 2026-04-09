from datetime import datetime, timedelta
from typing import Set
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY
from logger import logger

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_posted(days: int) -> Set[str]:
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        res = (
            supabase.table("posted_links")
            .select("link")
            .gte("posted_at", cutoff)
            .execute()
        )

        return {item["link"] for item in res.data} if res.data else set()

    except Exception as e:
        logger.error(f"Error loading links: {e}")
        return set()


def save_posted(link: str, feed_name: str, title: str) -> bool:
    try:
        data = {
            "link": link,
            "feed_name": feed_name,
            "title": title[:255],
            "posted_at": datetime.now().isoformat(),
        }

        res = supabase.table("posted_links").insert(data).execute()
        return bool(res.data)

    except Exception as e:
        if "duplicate key" in str(e).lower():
            return True

        logger.error(f"Error saving link: {e}")
        return False


def cleanup_old_links(days: int):
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        supabase.table("posted_links") \
            .delete() \
            .lt("posted_at", cutoff) \
            .execute()

        logger.info("Cleanup completed")

    except Exception as e:
        logger.error(f"Cleanup error: {e}")