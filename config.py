import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")

MAX_ITEMS_PER_FEED = 20
DAYS_TO_KEEP = 3

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN is required")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE credentials are required")