"""Scheduled tasks: traffic monitoring, expiry alerts, auto Xray restart."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from telegram.ext import ContextTypes

from config import ADMIN_CHAT_IDS, ENABLE_AUTO_RESTART
from utils.formatters import format_bytes, format_expiry

logger = logging.getLogger(__name__)


async def check_traffic_limits(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Periodic job: Check all clients for traffic limit violations.
    Only restart Xray and notify for NEW exceeded clients (not already notified).
    """
    api = context.bot_data.get("api")
    if not api:
        return

    try:
        result = await api.get_inbounds()
        if not result.get("success"):
            return

        inbounds = result.get("obj", [])
        # Track exceeded clients: email -> used bytes
        current_exceeded: dict[str, dict[str, Any]] = {}

        for inbound in inbounds:
            if not inbound.get("enable"):
                continue

            client_stats = inbound.get("clientStats") or []

            for stat in client_stats:
                total_limit = stat.get("total", 0)
                if total_limit <= 0:
                    continue  # Unlimited

                used = stat.get("up", 0) + stat.get("down", 0)
                if used > total_limit:
                    email = stat.get("email", "unknown")
                    current_exceeded[email] = {
                        "email": email,
                        "used": used,
                        "limit": total_limit,
                        "inbound_remark": inbound.get("remark", ""),
                    }

        # Get previously notified clients
        prev_exceeded = context.bot_data.get("_exceeded_clients", {})

        # Find NEW exceeded clients (not in previous check)
        new_exceeded = []
        for email, info in current_exceeded.items():
            if email not in prev_exceeded:
                new_exceeded.append(info)

        # Save current state for next check
        context.bot_data["_exceeded_clients"] = {
            email: info["used"] for email, info in current_exceeded.items()
        }

        if new_exceeded and ENABLE_AUTO_RESTART:
            # Restart Xray only for NEW exceeded clients
            await api.restart_xray()
            logger.info(
                "Auto-restarted Xray due to %d NEW client(s) exceeding traffic limits",
                len(new_exceeded),
            )

            # Notify admins only about new ones
            for admin_id in ADMIN_CHAT_IDS:
                for client in new_exceeded[:5]:
                    from lang import SCHED_TRAFFIC_ALERT
                    msg = SCHED_TRAFFIC_ALERT.format(
                        email=client["email"],
                        used=format_bytes(client["used"]),
                        limit=format_bytes(client["limit"]),
                    )
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=msg,
                            parse_mode="HTML",
                        )
                    except Exception as e:
                        logger.error("Failed to send traffic alert to %s: %s", admin_id, e)

                if len(new_exceeded) > 5:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=f"... و {len(new_exceeded) - 5} کاربر دیگر از حد مجاز فراتر رفته‌اند.",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

    except Exception as e:
        logger.error("Error in traffic check job: %s", e)


async def check_expiring_clients(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Periodic job: Check for clients expiring within 24 hours.
    Send a warning to admins.
    """
    api = context.bot_data.get("api")
    if not api:
        return

    try:
        result = await api.get_inbounds()
        if not result.get("success"):
            return

        inbounds = result.get("obj", [])
        now_ms = int(time.time() * 1000)
        threshold_ms = now_ms + (24 * 3600 * 1000)  # 24 hours from now

        expiring_clients: list[str] = []

        for inbound in inbounds:
            if not inbound.get("enable"):
                continue

            try:
                settings = json.loads(inbound.get("settings", "{}"))
                clients = settings.get("clients", [])
            except (json.JSONDecodeError, TypeError):
                continue

            for client in clients:
                if not client.get("enable", True):
                    continue

                expiry_time = client.get("expiryTime", 0)
                if expiry_time <= 0:
                    continue  # No expiry

                if now_ms < expiry_time <= threshold_ms:
                    email = client.get("email", "unknown")
                    remark = inbound.get("remark", "")
                    remaining_h = max(0, int((expiry_time - now_ms) / 3600000))
                    expiring_clients.append(
                        f"  • <code>{email}</code> ({remark}) — {remaining_h} ساعت مانده"
                    )

        if expiring_clients:
            from lang import SCHED_EXPIRY_ALERT
            clients_text = "\n".join(expiring_clients[:20])
            msg = SCHED_EXPIRY_ALERT.format(clients=clients_text)

            if len(expiring_clients) > 20:
                msg += f"\n\n... و {len(expiring_clients) - 20} کاربر دیگر"

            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=msg,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.error("Failed to send expiry alert to %s: %s", admin_id, e)

    except Exception as e:
        logger.error("Error in expiry check job: %s", e)


async def periodic_status_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Periodic job: Send server status report to admins.
    """
    api = context.bot_data.get("api")
    if not api:
        return

    try:
        result = await api.get_server_status()
        if not result.get("success"):
            return

        from utils.formatters import format_server_status
        from lang import SCHED_STATUS_REPORT

        # Also count online users
        online_result = await api.get_online_clients()
        online_count = 0
        if online_result.get("success"):
            online_list = online_result.get("obj") or []
            online_count = len(online_list)

        # Count total clients
        inb_result = await api.get_inbounds()
        total_clients = 0
        active_clients = 0
        if inb_result.get("success"):
            for inb in inb_result.get("obj", []):
                try:
                    settings = json.loads(inb.get("settings", "{}"))
                    clients = settings.get("clients", [])
                    total_clients += len(clients)
                    active_clients += sum(1 for c in clients if c.get("enable", True))
                except (json.JSONDecodeError, TypeError):
                    pass

        status_text = format_server_status(result)
        status_text += (
            f"\n\n👥 <b>کاربران:</b> {active_clients}/{total_clients} فعال"
            f"\n📡 <b>آنلاین:</b> {online_count} نفر"
        )

        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"{SCHED_STATUS_REPORT}\n\n{status_text}",
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error("Failed to send status report to %s: %s", admin_id, e)

    except Exception as e:
        logger.error("Error in status report job: %s", e)


def register_jobs(app) -> None:
    """Register all scheduled jobs with the application's job queue."""
    from config import TRAFFIC_CHECK_INTERVAL, EXPIRY_CHECK_INTERVAL

    job_queue = app.job_queue

    # Traffic limit checker
    job_queue.run_repeating(
        check_traffic_limits,
        interval=TRAFFIC_CHECK_INTERVAL,
        first=30,  # Start after 30 seconds
        name="traffic_checker",
    )
    logger.info(
        "📋 Traffic checker registered (every %d seconds)", TRAFFIC_CHECK_INTERVAL
    )

    # Expiry checker
    job_queue.run_repeating(
        check_expiring_clients,
        interval=EXPIRY_CHECK_INTERVAL,
        first=60,
        name="expiry_checker",
    )
    logger.info(
        "📋 Expiry checker registered (every %d seconds)", EXPIRY_CHECK_INTERVAL
    )

    # Status report (every 6 hours)
    job_queue.run_repeating(
        periodic_status_report,
        interval=21600,  # 6 hours
        first=120,
        name="status_report",
    )
    logger.info("📋 Periodic status report registered (every 6 hours)")
