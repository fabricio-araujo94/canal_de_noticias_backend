from datetime import datetime, timedelta


def is_recent(entry, max_days: int = 1) -> bool:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            return published >= datetime.now() - timedelta(days=max_days)
    except Exception:
        pass

    return True