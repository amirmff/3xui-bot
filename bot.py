"""
3x-ui Telegram Management Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full-featured Telegram bot for managing 3x-ui VPN panel(s).
Multi-panel support, Persian UI, proxy, scheduled monitoring.
"""

from __future__ import annotations

import logging
import sys

from telegram.ext import Application

from config import TELEGRAM_BOT_TOKEN, validate_config
from config import PANEL_URL, PANEL_USERNAME, PANEL_PASSWORD, PANEL_PATH, PROXY_URL
from api.client import XUIClient
from panels import PanelManager

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize the panel manager and connect to the active panel."""
    # Load panel manager
    pm = PanelManager()
    application.bot_data["panel_manager"] = pm

    # If no panels exist, create default from .env
    if pm.count() == 0 and PANEL_URL:
        api_base = f"{PANEL_URL.rstrip('/')}/{PANEL_PATH.strip('/')}" if PANEL_PATH else PANEL_URL.rstrip("/")
        panel = pm.ensure_default_panel(
            url=PANEL_URL,
            username=PANEL_USERNAME,
            password=PANEL_PASSWORD,
            path=PANEL_PATH,
            proxy_url=PROXY_URL,
        )
        if panel:
            logger.info("Default panel loaded: %s", panel.name)

    # Connect to the first available panel
    panels = pm.get_all_panels()
    if panels:
        panel = panels[0]
        api = XUIClient(
            base_url=panel.api_base,
            username=panel.username,
            password=panel.password,
            proxy_url=panel.proxy_url,
        )
        success = await api.login()
        if success:
            logger.info("✅ Connected to panel: %s (%s)", panel.name, panel.url)
        else:
            logger.error("❌ Failed to login to panel: %s", panel.name)

        application.bot_data["api"] = api
        application.bot_data["current_panel_id"] = panel.id
    else:
        logger.warning("⚠️ No panels configured. Add panels via the bot.")
        # Create a dummy API that will fail — user must add panels
        application.bot_data["api"] = XUIClient()
        application.bot_data["current_panel_id"] = ""


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    api = application.bot_data.get("api")
    if api:
        await api.close()
        logger.info("API session closed")


def main() -> None:
    """Start the bot."""
    # Validate config
    errors = validate_config()
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        print("\n❌ Configuration errors found! Check your .env file.")
        print("   Copy .env.example to .env and fill in the values.\n")
        sys.exit(1)

    logger.info("Starting 3x-ui Telegram Bot...")

    # Build application with job queue enabled
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Register all handlers
    from handlers import start, inbounds, clients, server, backup
    from handlers import panels as panels_handler

    start.register(app)
    inbounds.register(app)
    clients.register(app)
    server.register(app)
    backup.register(app)
    panels_handler.register(app)

    # Register scheduled jobs
    from scheduler import register_jobs
    register_jobs(app)

    logger.info("✅ All handlers registered (including panels)")
    logger.info("✅ Scheduled jobs registered")
    logger.info("🚀 Starting polling...")

    # Run the bot
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
