import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, Set

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not found in environment variables")
    raise ValueError("TELEGRAM_TOKEN is required")

CHANNEL = "@channel"
POSTED_FILE = "posted_links.txt"  # temporary
CHECK_INTERVAL = 600  # every 10 minutes
MAX_ITEMS_PER_FEED = 5


def load_posted() -> Set[str]:
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            links = set(f.read().splitlines())
        logger.info(f"Loaded {len(links)} links already published")
        return links
    except FileNotFoundError:
        logger.info("Archive of published links not found. Creating new one.")
        return set()
    except Exception as e:
        logger.error(f"Error loading links: {e}")
        return set()


def save_posted(link: str) -> bool:
    try:
        with open(POSTED_FILE, "a", encoding="utf-8") as f:
            f.write(link + "\n")
        return True
    except Exception as e:
        logger.error(f"Error saving link {link}: {e}")
        return False


def extract_image(entry: Dict[str, Any]) -> Optional[str]:
    try:
        if "media_content" in entry and entry.media_content:
            return entry.media_content[0]["url"]
        if "media_thumbnail" in entry and entry.media_thumbnail:
            return entry.media_thumbnail[0]["url"]
        if "summary" in entry and entry.summary:
            soup = BeautifulSoup(entry.summary, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return img["src"]
        if "content" in entry and entry.content:
            for content in entry.content:
                if "value" in content:
                    soup = BeautifulSoup(content.value)
                    img = soup.find("img")
                    if img and img.get("src"):
                        return img["src"]
        return None
    except Exception as e:
        logger.warning(f"Error extracting image: {e}")
        return None
