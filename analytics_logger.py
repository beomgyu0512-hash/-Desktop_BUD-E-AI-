import json
import os
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv


load_dotenv()

_LOG_LOCK = threading.Lock()


def get_analytics_path() -> str:
    configured_path = os.getenv("BUD_E_ANALYTICS_FILE", "analytics/events.jsonl").strip()
    if not os.path.isabs(configured_path):
        configured_path = os.path.abspath(configured_path)
    return configured_path


def ensure_analytics_dir() -> str:
    analytics_path = get_analytics_path()
    os.makedirs(os.path.dirname(analytics_path), exist_ok=True)
    return analytics_path


def _normalize_value(value):
    if isinstance(value, str):
        cleaned = " ".join(value.split())
        if len(cleaned) > 800:
            cleaned = cleaned[:800].rstrip()
        return cleaned
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    return value


def log_event(event_type: str, payload: dict | None = None) -> None:
    analytics_path = ensure_analytics_dir()
    event = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "event_type": event_type,
        "payload": _normalize_value(payload or {}),
    }

    with _LOG_LOCK:
        with open(analytics_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
