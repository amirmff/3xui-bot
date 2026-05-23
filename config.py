"""Configuration loader for 3x-ui Telegram Bot."""

import os
from dotenv import load_dotenv

load_dotenv()


TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
PANEL_URL: str = os.getenv("PANEL_URL", "").rstrip("/")
PANEL_USERNAME: str = os.getenv("PANEL_USERNAME", "admin")
PANEL_PASSWORD: str = os.getenv("PANEL_PASSWORD", "admin")
PANEL_PATH: str = os.getenv("PANEL_PATH", "").strip("/")

# Parse admin chat IDs
_raw_ids = os.getenv("ADMIN_CHAT_IDS", "")
ADMIN_CHAT_IDS: list[int] = [
    int(cid.strip()) for cid in _raw_ids.split(",") if cid.strip().isdigit()
]

# Proxy for connecting to panel (SOCKS5/HTTP)
PROXY_URL: str = os.getenv("PROXY_URL", "")

# Scheduler settings
TRAFFIC_CHECK_INTERVAL: int = int(os.getenv("TRAFFIC_CHECK_INTERVAL", "300"))
EXPIRY_CHECK_INTERVAL: int = int(os.getenv("EXPIRY_CHECK_INTERVAL", "3600"))
ENABLE_AUTO_RESTART: bool = os.getenv("ENABLE_AUTO_RESTART", "true").lower() == "true"

# Build base API URL
if PANEL_PATH:
    API_BASE = f"{PANEL_URL}/{PANEL_PATH}"
else:
    API_BASE = PANEL_URL


def validate_config() -> list[str]:
    """Return a list of missing/invalid config values."""
    errors: list[str] = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    if not PANEL_URL:
        errors.append("PANEL_URL is not set")
    if not ADMIN_CHAT_IDS:
        errors.append("ADMIN_CHAT_IDS is not set (no admin users)")
    return errors
