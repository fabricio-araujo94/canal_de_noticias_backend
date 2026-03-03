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
