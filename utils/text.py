import html
from bs4 import BeautifulSoup


def clean_summary(summary: str, max_length: int = 300) -> str:
    if not summary:
        return ""

    try:
        soup = BeautifulSoup(summary, "html.parser")
        text = " ".join(soup.get_text().split())

        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."

        return html.escape(text)

    except Exception:
        return html.escape(summary[:max_length])