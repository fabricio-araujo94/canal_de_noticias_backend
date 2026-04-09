import time
import requests

from config import TOKEN
from logger import logger


def send_message(session: requests.Session, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    for attempt in range(3):
        try:
            r = session.post(url, data=payload, timeout=10)

            if r.status_code == 200:
                return True

            logger.warning(f"Telegram error {r.status_code}: {r.text}")

        except requests.RequestException as e:
            logger.warning(f"Connection error: {e}")

        time.sleep(2**attempt)

    return False