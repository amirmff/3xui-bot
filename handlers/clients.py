"""Client management handlers — Persian UI with advanced features."""

from __future__ import annotations

import io
import json
import logging
import time
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters,
)

import lang
from handlers.common import (
    admin_only, get_api, back_button, answer_and_edit, send_or_edit,
    paginate_buttons, build_menu,
    CB_CLIENTS, CB_CLIENT_LIST, CB_CLIENT_VIEW, CB_CLIENT_ADD,
    CB_CLIENT_EDIT, CB_CLIENT_DEL, CB_CLIENT_LINK, CB_CLIENT_QR,
    CB_CLIENT_RESET_TRAFFIC, CB_CLIENT_TOGGLE,
    CB_CLIENT_IPS, CB_CLIENT_CLEAR_IPS,
    CB_CLIENT_ADD_DAYS, CB_CLIENT_ADD_TRAFFIC, CB_CLIENT_RENEW,
    CB_QUICK_TEMPLATE,
    CB_BULK_RESET_ALL, CB_BULK_RESET_INB, CB_BULK_DEL_DEPLETED,
    CB_BULK_ADD_DAYS, CB_BULK_ADD_TRAFFIC,
    CB_INBOUND_LIST, CB_MAIN_MENU,
)
from utils.formatters import format_client_detail, format_traffic, format_bytes, format_expiry
from utils.helpers import (
    generate_uuid, generate_password, generate_sub_id,
    gb_to_bytes, days_to_timestamp_ms, build_connection_link, generate_qr_code,
)
from config import PANEL_URL

logger = logging.getLogger(__name__)

_parsed = urlparse(PANEL_URL)
SERVER_ADDRESS = _parsed.hostname or "127.0.0.1"

# Conversation states
SELECT_INBOUND, ASK_EMAIL, ASK_TRAFFIC, ASK_EXPIRY, ASK_IP_LIMIT, CONFIRM_ADD = range(6)
EDIT_SELECT, EDIT_TRAFFIC, EDIT_EXPIRY, EDIT_IP_LIMIT = range(10, 14)
SEARCH_EMAIL = 20
ADD_DAYS_INPUT = 30
ADD_TRAFFIC_INPUT = 31
RENEW_INPUT = 32
BULK_DAYS_INPUT = 40
BULK_TRAFFIC_INPUT = 41
QUICK_SELECT_INB = 50
QUICK_ASK_EMAIL = 51


def _get_client_id(protocol: str, client: dict) -> str:
    """Get the appropriate client identifier based on protocol."""
    if protocol == "trojan":
        return client.get("password", client.get("id", ""))
    elif protocol == "shadowsocks":
        return client.get("email", "")
    return client.get("id", "")


# ─── Client Menu ──────────────────────────────────────────────────────────────

@admin_only
async def clients_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.CL_BROWSE, callback_data=CB_CLIENT_LIST)],
        [
            InlineKeyboardButton(lang.CL_ADD, callback_data=CB_CLIENT_ADD),
            InlineKeyboardButton(lang.QUICK_TEMPLATES, callback_data=CB_QUICK_TEMPLATE),
        ],
        [InlineKeyboardButton(lang.CL_SEARCH, callback_data="cl_search")],
        [
            InlineKeyboardButton(lang.BULK_RESET_ALL, callback_data=CB_BULK_RESET_ALL),
            InlineKeyboardButton(lang.BULK_DEL_DEPLETED, callback_data=f"{CB_BULK_DEL_DEPLETED}:-1"),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await answer_and_edit(update.callback_query, lang.CL_MANAGEMENT, reply_markup=keyboard)


@admin_only
async def clients_menu_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """From reply keyboard."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.CL_BROWSE, callback_data=CB_CLIENT_LIST)],
        [
            InlineKeyboardButton(lang.CL_ADD, callback_data=CB_CLIENT_ADD),
            InlineKeyboardButton(lang.QUICK_TEMPLATES, callback_data=CB_QUICK_TEMPLATE),
        ],
        [InlineKeyboardButton(lang.CL_SEARCH, callback_data="cl_search")],
        [
            InlineKeyboardButton(lang.BULK_RESET_ALL, callback_data=CB_BULK_RESET_ALL),
            InlineKeyboardButton(lang.BULK_DEL_DEPLETED, callback_data=f"{CB_BULK_DEL_DEPLETED}:-1"),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await update.message.reply_text(lang.CL_MANAGEMENT, reply_markup=keyboard, parse_mode="HTML")


# ─── Select Inbound ───────────────────────────────────────────────────────────

@admin_only
async def select_inbound_for_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    try:
        result = await api.get_inbounds()
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
            return

        inbounds = result.get("obj", [])
        if not inbounds:
            await query.edit_message_text("📋 هیچ اینباندی یافت نشد.",
                reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
            return

        items = []
        for inb in inbounds:
            status = "✅" if inb.get("enable") else "❌"
            protocol = inb.get("protocol", "?").upper()
            remark = inb.get("remark", "unnamed")
            try:
                settings = json.loads(inb.get("settings", "{}"))
                n = len(settings.get("clients", []))
            except:
                n = 0
            label = f"{status} {remark} | {protocol} ({n} کاربر)"
            items.append((label, f"cl_list_inb:{inb['id']}"))

        keyboard = paginate_buttons(items, page=0, per_page=8, n_cols=1, back_cb=CB_CLIENTS, page_prefix="cl_inb_page")
        await query.edit_message_text(lang.CL_SELECT_INBOUND, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


# ─── List Clients ─────────────────────────────────────────────────────────────

@admin_only
async def list_clients_for_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENT_LIST)]]), parse_mode="HTML")
            return

        inbound = result["obj"]
        remark = inbound.get("remark", "unnamed")
        try:
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
        except:
            clients = []

        client_stats = {s.get("email"): s for s in (inbound.get("clientStats") or [])}

        if not clients:
            await query.edit_message_text(
                lang.CL_LIST_EMPTY.format(remark=remark),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(lang.CL_ADD, callback_data=f"cl_add_inb:{inbound_id}")],
                    [back_button(CB_CLIENT_LIST)],
                ]), parse_mode="HTML")
            return

        page = 0
        if "cl_clients_page" in query.data:
            try:
                page = int(query.data.split(":")[2])
            except:
                page = 0

        items = []
        for cl in clients:
            email = cl.get("email", "unknown")
            enable = "✅" if cl.get("enable", True) else "❌"
            stat = client_stats.get(email, {})
            used = stat.get("up", 0) + stat.get("down", 0)
            label = f"{enable} {email} ({format_bytes(used)})"
            items.append((label, f"{CB_CLIENT_VIEW}:{inbound_id}:{email}"))

        keyboard = paginate_buttons(items, page=page, per_page=8, n_cols=1,
            back_cb=CB_CLIENT_LIST, page_prefix=f"cl_clients_page:{inbound_id}")

        # Bulk action buttons
        keyboard.inline_keyboard.insert(-1, [
            InlineKeyboardButton(lang.CL_ADD, callback_data=f"cl_add_inb:{inbound_id}"),
        ])
        keyboard.inline_keyboard.insert(-1, [
            InlineKeyboardButton(lang.BULK_ADD_DAYS_ALL, callback_data=f"{CB_BULK_ADD_DAYS}:{inbound_id}"),
            InlineKeyboardButton(lang.BULK_ADD_TRAFFIC_ALL, callback_data=f"{CB_BULK_ADD_TRAFFIC}:{inbound_id}"),
        ])
        keyboard.inline_keyboard.insert(-1, [
            InlineKeyboardButton(lang.BULK_RESET_INB, callback_data=f"{CB_BULK_RESET_INB}:{inbound_id}"),
            InlineKeyboardButton(lang.BULK_DEL_DEPLETED, callback_data=f"{CB_BULK_DEL_DEPLETED}:{inbound_id}"),
        ])

        await query.edit_message_text(
            lang.CL_LIST_TITLE.format(remark=remark, count=len(clients)),
            reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


# ─── View Client ──────────────────────────────────────────────────────────────

@admin_only
async def view_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except (ValueError, IndexError):
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return

        inbound = result["obj"]
        settings = json.loads(inbound.get("settings", "{}"))
        clients = settings.get("clients", [])
        client = next((c for c in clients if c.get("email") == email), None)

        if not client:
            await query.edit_message_text(lang.CL_NOT_FOUND.format(email=email),
                reply_markup=InlineKeyboardMarkup([[back_button(f"cl_list_inb:{inbound_id}")]]), parse_mode="HTML")
            return

        stat = next((s for s in (inbound.get("clientStats") or []) if s.get("email") == email), None)
        text = format_client_detail(client, stat)

        enable_text = "❌ غیرفعال" if client.get("enable", True) else "✅ فعال"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 لینک", callback_data=f"{CB_CLIENT_LINK}:{inbound_id}:{email}"),
                InlineKeyboardButton("📱 QR", callback_data=f"{CB_CLIENT_QR}:{inbound_id}:{email}"),
            ],
            [
                InlineKeyboardButton(enable_text, callback_data=f"{CB_CLIENT_TOGGLE}:{inbound_id}:{email}"),
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"{CB_CLIENT_EDIT}:{inbound_id}:{email}"),
            ],
            [
                InlineKeyboardButton(lang.CL_ADD_DAYS, callback_data=f"{CB_CLIENT_ADD_DAYS}:{inbound_id}:{email}"),
                InlineKeyboardButton(lang.CL_ADD_TRAFFIC_VOL, callback_data=f"{CB_CLIENT_ADD_TRAFFIC}:{inbound_id}:{email}"),
            ],
            [
                InlineKeyboardButton(lang.CL_RENEW, callback_data=f"{CB_CLIENT_RENEW}:{inbound_id}:{email}"),
                InlineKeyboardButton("🔄 ریست ترافیک", callback_data=f"{CB_CLIENT_RESET_TRAFFIC}:{inbound_id}:{email}"),
            ],
            [
                InlineKeyboardButton("🌐 آی‌پی‌ها", callback_data=f"{CB_CLIENT_IPS}:{inbound_id}:{email}"),
                InlineKeyboardButton("🗑 حذف", callback_data=f"{CB_CLIENT_DEL}:{inbound_id}:{email}"),
            ],
            [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
            [back_button(f"cl_list_inb:{inbound_id}")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


# ─── Connection Link & QR ─────────────────────────────────────────────────────

@admin_only
async def client_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            return

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            await query.edit_message_text(lang.CL_NOT_FOUND.format(email=email), parse_mode="HTML")
            return

        link = build_connection_link(protocol, SERVER_ADDRESS, inbound, client)
        await query.edit_message_text(
            f"{lang.CL_LINK_TITLE}\n\n<b>کاربر:</b> {email}\n<b>پروتکل:</b> {protocol.upper()}\n\n<code>{link}</code>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 QR Code", callback_data=f"{CB_CLIENT_QR}:{inbound_id}:{email}")],
                [back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
            ]), parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


@admin_only
async def client_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال ساخت QR...")
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            return

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            return

        link = build_connection_link(protocol, SERVER_ADDRESS, inbound, client)
        qr_bytes = generate_qr_code(link)
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=InputFile(io.BytesIO(qr_bytes), filename=f"{email}_qr.png"),
            caption=f"📱 <b>QR Code</b>\n\n<b>کاربر:</b> {email}\n\n<code>{link}</code>",
            parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=lang.ERROR.format(error=e), parse_mode="HTML")


# ─── Toggle / IPs / Reset Traffic / Delete ─────────────────────────────────────

@admin_only
async def toggle_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            return

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            return

        client["enable"] = not client.get("enable", True)
        client_id = _get_client_id(protocol, client)
        upd = await api.update_client(client_id, inbound_id, client)

        if upd.get("success"):
            text = lang.CL_TOGGLE_ENABLED.format(email=email) if client["enable"] else lang.CL_TOGGLE_DISABLED.format(email=email)
        else:
            text = lang.FAILED.format(msg=upd.get("msg", ""))

        await query.edit_message_text(text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 مشاهده", callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
                [back_button(f"cl_list_inb:{inbound_id}")],
            ]), parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


@admin_only
async def client_ips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    result = await api.get_client_ips(email)
    if result.get("success"):
        ips = result.get("obj", "")
        text = f"🌐 <b>آی‌پی‌های {email}</b>\n\n<pre>{ips}</pre>" if ips and ips != "No IP Record" else lang.CL_IPS_EMPTY.format(email=email)
    else:
        text = lang.FAILED.format(msg=result.get("msg", ""))

    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧹 پاک کردن", callback_data=f"{CB_CLIENT_CLEAR_IPS}:{inbound_id}:{email}")],
            [back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
        ]), parse_mode="HTML")


@admin_only
async def clear_client_ips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    result = await api.clear_client_ips(email)
    text = lang.CL_IPS_CLEARED.format(email=email) if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")


@admin_only
async def reset_traffic_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    await query.edit_message_text(
        lang.CL_RESET_TRAFFIC_CONFIRM.format(email=email),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data=f"cl_reset_yes:{inbound_id}:{email}"),
                InlineKeyboardButton(lang.BTN_CANCEL, callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}"),
            ],
        ]), parse_mode="HTML")


@admin_only
async def reset_traffic_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    result = await api.reset_client_traffic(inbound_id, email)
    text = lang.CL_RESET_TRAFFIC_SUCCESS.format(email=email) if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")


@admin_only
async def delete_client_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    await query.edit_message_text(
        lang.CL_DELETE_CONFIRM.format(email=email),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data=f"cl_del_yes:{inbound_id}:{email}"),
                InlineKeyboardButton(lang.BTN_CANCEL, callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}"),
            ],
        ]), parse_mode="HTML")


@admin_only
async def delete_client_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            return
        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            return

        client_id = _get_client_id(protocol, client)
        del_result = await api.delete_client(inbound_id, client_id)
        text = lang.CL_DELETE_SUCCESS.format(email=email) if del_result.get("success") else lang.FAILED.format(msg=del_result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"cl_list_inb:{inbound_id}")]]), parse_mode="HTML")


# ─── Add Days to Client ───────────────────────────────────────────────────────

@admin_only
async def add_days_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return ConversationHandler.END

    context.user_data["op_client"] = {"inbound_id": inbound_id, "email": email, "action": "add_days"}
    await query.edit_message_text(lang.CL_ADD_DAYS_PROMPT.format(email=email), parse_mode="HTML")
    return ADD_DAYS_INPUT


@admin_only
async def add_days_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        days = int(update.message.text.strip())
        if days <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ADD_DAYS_INPUT

    data = context.user_data.get("op_client", {})
    inbound_id = data["inbound_id"]
    email = data["email"]

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            await update.message.reply_text(lang.CL_NOT_FOUND.format(email=email), parse_mode="HTML")
            return ConversationHandler.END

        # Add days to expiry
        current_expiry = client.get("expiryTime", 0)
        now_ms = int(time.time() * 1000)
        if current_expiry <= 0 or current_expiry < now_ms:
            # No expiry or already expired — start from now
            new_expiry = now_ms + (days * 86400 * 1000)
        else:
            # Add to existing expiry
            new_expiry = current_expiry + (days * 86400 * 1000)

        client["expiryTime"] = new_expiry
        client_id = _get_client_id(protocol, client)
        upd = await api.update_client(client_id, inbound_id, client)

        if upd.get("success"):
            text = lang.CL_ADD_DAYS_SUCCESS.format(days=days, email=email, new_expiry=format_expiry(new_expiry))
        else:
            text = lang.FAILED.format(msg=upd.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")
    context.user_data.pop("op_client", None)
    return ConversationHandler.END


# ─── Add Traffic to Client ────────────────────────────────────────────────────

@admin_only
async def add_traffic_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return ConversationHandler.END

    context.user_data["op_client"] = {"inbound_id": inbound_id, "email": email, "action": "add_traffic"}
    await query.edit_message_text(lang.CL_ADD_TRAFFIC_PROMPT.format(email=email), parse_mode="HTML")
    return ADD_TRAFFIC_INPUT


@admin_only
async def add_traffic_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gb = float(update.message.text.strip())
        if gb <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ADD_TRAFFIC_INPUT

    data = context.user_data.get("op_client", {})
    inbound_id = data["inbound_id"]
    email = data["email"]

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            await update.message.reply_text(lang.CL_NOT_FOUND.format(email=email), parse_mode="HTML")
            return ConversationHandler.END

        current_total = client.get("totalGB", 0)
        add_bytes = gb_to_bytes(gb)
        new_total = current_total + add_bytes
        client["totalGB"] = new_total

        client_id = _get_client_id(protocol, client)
        upd = await api.update_client(client_id, inbound_id, client)

        if upd.get("success"):
            text = lang.CL_ADD_TRAFFIC_SUCCESS.format(gb=gb, email=email, new_total=format_bytes(new_total))
        else:
            text = lang.FAILED.format(msg=upd.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")
    context.user_data.pop("op_client", None)
    return ConversationHandler.END


# ─── Renew Client ─────────────────────────────────────────────────────────────

@admin_only
async def renew_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return ConversationHandler.END

    context.user_data["op_client"] = {"inbound_id": inbound_id, "email": email, "action": "renew"}
    await query.edit_message_text(lang.CL_RENEW_PROMPT.format(email=email), parse_mode="HTML")
    return RENEW_INPUT


@admin_only
async def renew_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_input = update.message.text.strip().split()
    try:
        if len(text_input) < 2:
            raise ValueError()
        gb = float(text_input[0])
        days = int(text_input[1])
        if gb < 0 or days < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ فرمت نامعتبر. مثال: <code>50 30</code>", parse_mode="HTML")
        return RENEW_INPUT

    data = context.user_data.get("op_client", {})
    inbound_id = data["inbound_id"]
    email = data["email"]

    api = get_api(context)
    try:
        # Reset traffic first
        await api.reset_client_traffic(inbound_id, email)

        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            await update.message.reply_text(lang.CL_NOT_FOUND.format(email=email), parse_mode="HTML")
            return ConversationHandler.END

        client["totalGB"] = gb_to_bytes(gb) if gb > 0 else 0
        client["expiryTime"] = days_to_timestamp_ms(days)
        client["enable"] = True

        client_id = _get_client_id(protocol, client)
        upd = await api.update_client(client_id, inbound_id, client)

        if upd.get("success"):
            text = lang.CL_RENEW_SUCCESS.format(email=email, gb=gb, days=days)
        else:
            text = lang.FAILED.format(msg=upd.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")
    context.user_data.pop("op_client", None)
    return ConversationHandler.END


# ─── Quick Template ────────────────────────────────────────────────────────────

@admin_only
async def quick_template_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    buttons = []
    for i, t in enumerate(lang.TEMPLATES):
        buttons.append(InlineKeyboardButton(t["label"], callback_data=f"qt_sel:{i}"))
    rows = build_menu(buttons, n_cols=1)
    rows.append([InlineKeyboardButton(lang.BTN_CANCEL, callback_data="qt_cancel")])

    await query.edit_message_text(lang.QUICK_TEMPLATE_LIST, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
    return QUICK_SELECT_INB


@admin_only
async def quick_template_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        idx = int(query.data.split(":")[1])
        template = lang.TEMPLATES[idx]
    except:
        return ConversationHandler.END

    context.user_data["quick_template"] = template

    # Show inbounds to select
    api = get_api(context)
    result = await api.get_inbounds()
    if not result.get("success"):
        await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
        return ConversationHandler.END

    inbounds = result.get("obj", [])
    buttons = []
    for inb in inbounds:
        protocol = inb.get("protocol", "?").upper()
        remark = inb.get("remark", "unnamed")
        buttons.append(InlineKeyboardButton(f"{remark} ({protocol})", callback_data=f"qt_inb:{inb['id']}"))
    rows = build_menu(buttons, n_cols=1)
    rows.append([InlineKeyboardButton(lang.BTN_CANCEL, callback_data="qt_cancel")])

    await query.edit_message_text(
        f"⚡ قالب: <b>{template['label']}</b>\n\nاینباند را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
    return QUICK_SELECT_INB


@admin_only
async def quick_template_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except:
        return ConversationHandler.END

    context.user_data["quick_template"]["inbound_id"] = inbound_id
    await query.edit_message_text(
        f"⚡ <b>ساخت سریع</b>\n\n<b>ایمیل/نام کاربری</b> وارد کنید:", parse_mode="HTML")
    return QUICK_ASK_EMAIL


@admin_only
async def quick_template_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not email or " " in email:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return QUICK_ASK_EMAIL

    t = context.user_data.get("quick_template", {})
    inbound_id = t.get("inbound_id")

    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")

        client_dict = {
            "email": email, "enable": True,
            "totalGB": gb_to_bytes(t.get("gb", 0)) if t.get("gb", 0) > 0 else 0,
            "expiryTime": days_to_timestamp_ms(t.get("days", 30)),
            "limitIp": t.get("ip", 0),
            "tgId": "", "subId": generate_sub_id(), "reset": 0,
        }

        if protocol in ("vmess", "vless"):
            client_dict["id"] = generate_uuid()
            client_dict["flow"] = ""
        elif protocol == "trojan":
            client_dict["id"] = generate_uuid()
            client_dict["password"] = generate_password()
        elif protocol == "shadowsocks":
            client_dict["password"] = generate_password()

        add_result = await api.add_client(inbound_id, [client_dict])
        if add_result.get("success"):
            text = (
                f"✅ <b>کاربر {email} ساخته شد!</b>\n\n"
                f"📦 حجم: {t.get('gb', 0)} GB\n"
                f"📅 مدت: {t.get('days', 30)} روز\n"
                f"🌐 IP: {t.get('ip', 0) or '♾'}"
            )
        else:
            text = lang.FAILED.format(msg=add_result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 مشاهده", callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
            [back_button(CB_CLIENTS)],
        ]), parse_mode="HTML")
    context.user_data.pop("quick_template", None)
    return ConversationHandler.END


async def quick_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("quick_template", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(lang.OPERATION_CANCELLED,
            reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
    return ConversationHandler.END


# ─── Add Client Conversation ──────────────────────────────────────────────────

@admin_only
async def add_client_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    result = await api.get_inbounds()
    if not result.get("success") or not result.get("obj"):
        await query.edit_message_text("❌ اینباندی یافت نشد.", parse_mode="HTML")
        return ConversationHandler.END

    buttons = []
    for inb in result["obj"]:
        buttons.append(InlineKeyboardButton(f"{inb.get('remark', '')} ({inb.get('protocol', '').upper()})", callback_data=f"add_cl_inb:{inb['id']}"))
    rows = build_menu(buttons, n_cols=1)
    rows.append([InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_cl_cancel")])

    await query.edit_message_text(lang.CL_ADD_SELECT_INB, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
    return SELECT_INBOUND


@admin_only
async def add_client_start_with_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except:
        return ConversationHandler.END

    api = get_api(context)
    result = await api.get_inbound(inbound_id)
    if not result.get("success"):
        return ConversationHandler.END

    inbound = result["obj"]
    context.user_data["new_client"] = {
        "inbound_id": inbound_id, "protocol": inbound.get("protocol", ""),
        "inbound_remark": inbound.get("remark", ""),
    }
    await query.edit_message_text(
        f"➕ <b>افزودن کاربر به: {inbound.get('remark', '')}</b>\n\n{lang.CL_ADD_EMAIL}", parse_mode="HTML")
    return ASK_EMAIL


@admin_only
async def add_client_select_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except:
        return ConversationHandler.END

    api = get_api(context)
    result = await api.get_inbound(inbound_id)
    if not result.get("success"):
        return ConversationHandler.END

    inbound = result["obj"]
    context.user_data["new_client"] = {
        "inbound_id": inbound_id, "protocol": inbound.get("protocol", ""),
        "inbound_remark": inbound.get("remark", ""),
    }
    await query.edit_message_text(
        f"➕ <b>افزودن کاربر به: {inbound.get('remark', '')}</b>\n\n{lang.CL_ADD_EMAIL}", parse_mode="HTML")
    return ASK_EMAIL


@admin_only
async def add_client_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not email or len(email) > 50 or " " in email:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_EMAIL
    context.user_data["new_client"]["email"] = email
    await update.message.reply_text(f"ایمیل: <b>{email}</b>\n\n{lang.CL_ADD_TRAFFIC}", parse_mode="HTML")
    return ASK_TRAFFIC


@admin_only
async def add_client_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gb = float(update.message.text.strip())
        if gb < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_TRAFFIC
    context.user_data["new_client"]["traffic_gb"] = gb
    await update.message.reply_text(f"حجم: <b>{gb} GB</b>\n\n{lang.CL_ADD_EXPIRY}", parse_mode="HTML")
    return ASK_EXPIRY


@admin_only
async def add_client_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        days = int(update.message.text.strip())
        if days < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_EXPIRY
    context.user_data["new_client"]["expiry_days"] = days
    await update.message.reply_text(f"مدت: <b>{days} روز</b>\n\n{lang.CL_ADD_IP_LIMIT}", parse_mode="HTML")
    return ASK_IP_LIMIT


@admin_only
async def add_client_ip_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        ip_limit = int(update.message.text.strip())
        if ip_limit < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_IP_LIMIT

    data = context.user_data["new_client"]
    data["ip_limit"] = ip_limit

    traffic_str = f"{data['traffic_gb']} GB" if data['traffic_gb'] > 0 else lang.FMT_UNLIMITED
    expiry_str = f"{data['expiry_days']} روز" if data['expiry_days'] > 0 else lang.FMT_NEVER
    ip_str = str(ip_limit) if ip_limit > 0 else lang.FMT_UNLIMITED

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ایجاد", callback_data="add_cl_confirm"),
         InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_cl_cancel")],
    ])
    await update.message.reply_text(
        f"{lang.CL_ADD_CONFIRM}\n\n<b>اینباند:</b> {data.get('inbound_remark', '')}\n"
        f"<b>ایمیل:</b> {data['email']}\n<b>حجم:</b> {traffic_str}\n"
        f"<b>مدت:</b> {expiry_str}\n<b>IP:</b> {ip_str}",
        reply_markup=keyboard, parse_mode="HTML")
    return CONFIRM_ADD


@admin_only
async def add_client_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data.get("new_client", {})

    client_dict = {
        "email": data.get("email", ""), "enable": True,
        "totalGB": gb_to_bytes(data.get("traffic_gb", 0)) if data.get("traffic_gb", 0) > 0 else 0,
        "expiryTime": days_to_timestamp_ms(data.get("expiry_days", 0)),
        "limitIp": data.get("ip_limit", 0),
        "tgId": "", "subId": generate_sub_id(), "reset": 0,
    }

    protocol = data.get("protocol", "")
    if protocol in ("vmess", "vless"):
        client_dict["id"] = generate_uuid()
        client_dict["flow"] = ""
    elif protocol == "trojan":
        client_dict["id"] = generate_uuid()
        client_dict["password"] = generate_password()
    elif protocol == "shadowsocks":
        client_dict["password"] = generate_password()

    api = get_api(context)
    inbound_id = data.get("inbound_id")
    try:
        result = await api.add_client(inbound_id, [client_dict])
        if result.get("success"):
            text = f"{lang.CL_ADD_SUCCESS}\n\n<b>ایمیل:</b> <code>{data['email']}</code>"
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 مشاهده", callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{data.get('email', '')}")],
            [back_button(CB_CLIENTS)],
        ]), parse_mode="HTML")
    context.user_data.pop("new_client", None)
    return ConversationHandler.END


async def add_client_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_client", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(lang.CL_ADD_CANCEL,
            reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
    elif update.message:
        await update.message.reply_text(lang.CL_ADD_CANCEL,
            reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
    return ConversationHandler.END


# ─── Edit Client ──────────────────────────────────────────────────────────────

@admin_only
async def edit_client_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split(":")
        inbound_id = int(parts[1])
        email = ":".join(parts[2:])
    except:
        return ConversationHandler.END

    context.user_data["edit_client"] = {"inbound_id": inbound_id, "email": email}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 حد ترافیک", callback_data="edit_cl_traffic")],
        [InlineKeyboardButton("📅 تاریخ انقضا", callback_data="edit_cl_expiry")],
        [InlineKeyboardButton("🌐 محدودیت IP", callback_data="edit_cl_ip")],
        [InlineKeyboardButton(lang.BTN_CANCEL, callback_data="edit_cl_cancel")],
    ])
    await query.edit_message_text(f"✏️ <b>ویرایش کاربر: {email}</b>\n\nچه چیزی را تغییر دهم؟",
        reply_markup=keyboard, parse_mode="HTML")
    return EDIT_SELECT


@admin_only
async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data
    if action == "edit_cl_traffic":
        await query.edit_message_text("📦 <b>حد ترافیک جدید (GB)</b> وارد کنید (0 = نامحدود):", parse_mode="HTML")
        return EDIT_TRAFFIC
    elif action == "edit_cl_expiry":
        await query.edit_message_text("📅 <b>مدت جدید (روز)</b> از الان وارد کنید (0 = بدون انقضا):", parse_mode="HTML")
        return EDIT_EXPIRY
    elif action == "edit_cl_ip":
        await query.edit_message_text("🌐 <b>محدودیت IP جدید</b> وارد کنید (0 = نامحدود):", parse_mode="HTML")
        return EDIT_IP_LIMIT
    return EDIT_SELECT


@admin_only
async def edit_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gb = float(update.message.text.strip())
        if gb < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return EDIT_TRAFFIC
    return await _apply_edit(update, context, "totalGB", gb_to_bytes(gb) if gb > 0 else 0)


@admin_only
async def edit_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        days = int(update.message.text.strip())
        if days < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return EDIT_EXPIRY
    return await _apply_edit(update, context, "expiryTime", days_to_timestamp_ms(days))


@admin_only
async def edit_ip_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        ip = int(update.message.text.strip())
        if ip < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return EDIT_IP_LIMIT
    return await _apply_edit(update, context, "limitIp", ip)


async def _apply_edit(update, context, field, value) -> int:
    data = context.user_data.get("edit_client", {})
    inbound_id = data.get("inbound_id")
    email = data.get("email")
    api = get_api(context)
    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        client = next((c for c in settings.get("clients", []) if c.get("email") == email), None)
        if not client:
            await update.message.reply_text(lang.CL_NOT_FOUND.format(email=email), parse_mode="HTML")
            return ConversationHandler.END

        client[field] = value
        client_id = _get_client_id(protocol, client)
        upd = await api.update_client(client_id, inbound_id, client)

        text = f"✅ <code>{email}</code> آپدیت شد!" if upd.get("success") else lang.FAILED.format(msg=upd.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")]]), parse_mode="HTML")
    context.user_data.pop("edit_client", None)
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("edit_client", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(lang.OPERATION_CANCELLED,
            reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
    return ConversationHandler.END


# ─── Search Client ─────────────────────────────────────────────────────────────

@admin_only
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(lang.CL_SEARCH_TITLE, parse_mode="HTML")
    return SEARCH_EMAIL


@admin_only
async def search_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not email:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return SEARCH_EMAIL

    api = get_api(context)
    result = await api.get_client_traffics(email)
    if result.get("success") and result.get("obj"):
        obj = result["obj"]
        inbound_id = obj.get("inboundId", 0)
        text = (
            f"🔍 <b>نتیجه جستجو: {email}</b>\n\n"
            f"<b>وضعیت:</b> {'✅ فعال' if obj.get('enable', True) else '❌ غیرفعال'}\n"
            f"<b>اینباند:</b> {inbound_id}\n\n"
            f"<b>ترافیک:</b>\n{format_traffic(obj.get('up', 0), obj.get('down', 0), obj.get('total', 0))}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 مشاهده", callback_data=f"{CB_CLIENT_VIEW}:{inbound_id}:{email}")],
            [back_button(CB_CLIENTS)],
        ])
    else:
        text = lang.CL_SEARCH_NOT_FOUND.format(email=email)
        keyboard = InlineKeyboardMarkup([[back_button(CB_CLIENTS)]])

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    return ConversationHandler.END


async def search_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(lang.OPERATION_CANCELLED,
        reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")
    return ConversationHandler.END


# ─── Bulk Operations ──────────────────────────────────────────────────────────

@admin_only
async def bulk_reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(lang.BULK_RESET_ALL_CONFIRM,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data="bulk_reset_all_yes"),
             InlineKeyboardButton(lang.BTN_CANCEL, callback_data=CB_CLIENTS)],
        ]), parse_mode="HTML")


@admin_only
async def bulk_reset_all_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    result = await api.reset_all_traffics()
    text = lang.BULK_RESET_ALL_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_CLIENTS)]]), parse_mode="HTML")


@admin_only
async def bulk_reset_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    inbound_id = int(query.data.split(":")[1])
    api = get_api(context)
    result = await api.reset_all_client_traffics(inbound_id)
    text = "✅ ترافیک همه کاربران این اینباند ریست شد!" if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(f"cl_list_inb:{inbound_id}")]]), parse_mode="HTML")


@admin_only
async def bulk_delete_depleted(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    inbound_id = int(query.data.split(":")[1])
    api = get_api(context)
    result = await api.delete_depleted_clients(inbound_id)
    text = "✅ کاربران تمام‌شده حذف شدند!" if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    back_cb = CB_CLIENTS if inbound_id == -1 else f"cl_list_inb:{inbound_id}"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(back_cb)]]), parse_mode="HTML")


# ─── Bulk Add Days ─────────────────────────────────────────────────────────────

@admin_only
async def bulk_add_days_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    inbound_id = int(query.data.split(":")[1])
    context.user_data["bulk_op"] = {"inbound_id": inbound_id, "action": "add_days"}
    await query.edit_message_text(lang.BULK_ADD_DAYS_PROMPT, parse_mode="HTML")
    return BULK_DAYS_INPUT


@admin_only
async def bulk_add_days_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        days = int(update.message.text.strip())
        if days <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return BULK_DAYS_INPUT

    data = context.user_data.get("bulk_op", {})
    inbound_id = data["inbound_id"]
    api = get_api(context)

    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        clients = settings.get("clients", [])
        now_ms = int(time.time() * 1000)
        count = 0

        for client in clients:
            current_expiry = client.get("expiryTime", 0)
            if current_expiry <= 0 or current_expiry < now_ms:
                new_expiry = now_ms + (days * 86400 * 1000)
            else:
                new_expiry = current_expiry + (days * 86400 * 1000)
            client["expiryTime"] = new_expiry

            client_id = _get_client_id(protocol, client)
            upd = await api.update_client(client_id, inbound_id, client)
            if upd.get("success"):
                count += 1

        text = lang.BULK_ADD_DAYS_SUCCESS.format(days=days, count=count)
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"cl_list_inb:{inbound_id}")]]), parse_mode="HTML")
    context.user_data.pop("bulk_op", None)
    return ConversationHandler.END


# ─── Bulk Add Traffic ──────────────────────────────────────────────────────────

@admin_only
async def bulk_add_traffic_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    inbound_id = int(query.data.split(":")[1])
    context.user_data["bulk_op"] = {"inbound_id": inbound_id, "action": "add_traffic"}
    await query.edit_message_text(lang.BULK_ADD_TRAFFIC_PROMPT, parse_mode="HTML")
    return BULK_TRAFFIC_INPUT


@admin_only
async def bulk_add_traffic_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gb = float(update.message.text.strip())
        if gb <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return BULK_TRAFFIC_INPUT

    data = context.user_data.get("bulk_op", {})
    inbound_id = data["inbound_id"]
    api = get_api(context)

    try:
        result = await api.get_inbound(inbound_id)
        if not result.get("success"):
            await update.message.reply_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return ConversationHandler.END

        inbound = result["obj"]
        protocol = inbound.get("protocol", "")
        settings = json.loads(inbound.get("settings", "{}"))
        clients = settings.get("clients", [])
        add_bytes = gb_to_bytes(gb)
        count = 0

        for client in clients:
            current = client.get("totalGB", 0)
            client["totalGB"] = current + add_bytes

            client_id = _get_client_id(protocol, client)
            upd = await api.update_client(client_id, inbound_id, client)
            if upd.get("success"):
                count += 1

        text = lang.BULK_ADD_TRAFFIC_SUCCESS.format(gb=gb, count=count)
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(f"cl_list_inb:{inbound_id}")]]), parse_mode="HTML")
    context.user_data.pop("bulk_op", None)
    return ConversationHandler.END


async def bulk_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("bulk_op", None)
    if update.message:
        await update.message.reply_text(lang.OPERATION_CANCELLED, parse_mode="HTML")
    return ConversationHandler.END


# ─── Register ─────────────────────────────────────────────────────────────────

def register(app) -> None:
    app.add_handler(CallbackQueryHandler(clients_menu, pattern=f"^{CB_CLIENTS}$"))
    app.add_handler(CallbackQueryHandler(select_inbound_for_clients, pattern=f"^{CB_CLIENT_LIST}$"))
    app.add_handler(CallbackQueryHandler(list_clients_for_inbound, pattern=r"^cl_list_inb:\d+$"))
    app.add_handler(CallbackQueryHandler(list_clients_for_inbound, pattern=r"^cl_clients_page:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(view_client, pattern=rf"^{CB_CLIENT_VIEW}:\d+:"))
    app.add_handler(CallbackQueryHandler(client_link, pattern=rf"^{CB_CLIENT_LINK}:\d+:"))
    app.add_handler(CallbackQueryHandler(client_qr, pattern=rf"^{CB_CLIENT_QR}:\d+:"))
    app.add_handler(CallbackQueryHandler(client_ips, pattern=rf"^{CB_CLIENT_IPS}:\d+:"))
    app.add_handler(CallbackQueryHandler(clear_client_ips, pattern=rf"^{CB_CLIENT_CLEAR_IPS}:\d+:"))
    app.add_handler(CallbackQueryHandler(toggle_client, pattern=rf"^{CB_CLIENT_TOGGLE}:\d+:"))
    app.add_handler(CallbackQueryHandler(reset_traffic_confirm, pattern=rf"^{CB_CLIENT_RESET_TRAFFIC}:\d+:"))
    app.add_handler(CallbackQueryHandler(reset_traffic_execute, pattern=r"^cl_reset_yes:\d+:"))
    app.add_handler(CallbackQueryHandler(delete_client_confirm, pattern=rf"^{CB_CLIENT_DEL}:\d+:"))
    app.add_handler(CallbackQueryHandler(delete_client_execute, pattern=r"^cl_del_yes:\d+:"))

    app.add_handler(CallbackQueryHandler(bulk_reset_all, pattern=f"^{CB_BULK_RESET_ALL}$"))
    app.add_handler(CallbackQueryHandler(bulk_reset_all_execute, pattern=r"^bulk_reset_all_yes$"))
    app.add_handler(CallbackQueryHandler(bulk_reset_inbound, pattern=rf"^{CB_BULK_RESET_INB}:\d+$"))
    app.add_handler(CallbackQueryHandler(bulk_delete_depleted, pattern=rf"^{CB_BULK_DEL_DEPLETED}:-?\d+$"))

    # Add client
    add_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_client_start, pattern=f"^{CB_CLIENT_ADD}$"),
            CallbackQueryHandler(add_client_start_with_inbound, pattern=r"^cl_add_inb:\d+$"),
        ],
        states={
            SELECT_INBOUND: [CallbackQueryHandler(add_client_select_inbound, pattern=r"^add_cl_inb:\d+$")],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_client_email)],
            ASK_TRAFFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_client_traffic)],
            ASK_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_client_expiry)],
            ASK_IP_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_client_ip_limit)],
            CONFIRM_ADD: [CallbackQueryHandler(add_client_execute, pattern=r"^add_cl_confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(add_client_cancel, pattern=r"^add_cl_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), add_client_cancel),
        ],
        per_message=False,
    )
    app.add_handler(add_conv)

    # Edit client
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_client_start, pattern=rf"^{CB_CLIENT_EDIT}:\d+:")],
        states={
            EDIT_SELECT: [CallbackQueryHandler(edit_select, pattern=r"^edit_cl_")],
            EDIT_TRAFFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_traffic)],
            EDIT_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_expiry)],
            EDIT_IP_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ip_limit)],
        },
        fallbacks=[
            CallbackQueryHandler(edit_cancel, pattern=r"^edit_cl_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), edit_cancel),
        ],
        per_message=False,
    )
    app.add_handler(edit_conv)

    # Search
    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_start, pattern=r"^cl_search$")],
        states={SEARCH_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_email)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), search_cancel)],
        per_message=False,
    )
    app.add_handler(search_conv)

    # Add days
    add_days_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_days_start, pattern=rf"^{CB_CLIENT_ADD_DAYS}:\d+:")],
        states={ADD_DAYS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_days_execute)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), bulk_cancel)],
        per_message=False,
    )
    app.add_handler(add_days_conv)

    # Add traffic
    add_traffic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_traffic_start, pattern=rf"^{CB_CLIENT_ADD_TRAFFIC}:\d+:")],
        states={ADD_TRAFFIC_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_traffic_execute)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), bulk_cancel)],
        per_message=False,
    )
    app.add_handler(add_traffic_conv)

    # Renew
    renew_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(renew_start, pattern=rf"^{CB_CLIENT_RENEW}:\d+:")],
        states={RENEW_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_execute)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), bulk_cancel)],
        per_message=False,
    )
    app.add_handler(renew_conv)

    # Quick template
    quick_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(quick_template_start, pattern=f"^{CB_QUICK_TEMPLATE}$")],
        states={
            QUICK_SELECT_INB: [
                CallbackQueryHandler(quick_template_select, pattern=r"^qt_sel:\d+$"),
                CallbackQueryHandler(quick_template_inbound, pattern=r"^qt_inb:\d+$"),
            ],
            QUICK_ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, quick_template_email)],
        },
        fallbacks=[
            CallbackQueryHandler(quick_cancel, pattern=r"^qt_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), quick_cancel),
        ],
        per_message=False,
    )
    app.add_handler(quick_conv)

    # Bulk add days/traffic
    bulk_days_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bulk_add_days_start, pattern=rf"^{CB_BULK_ADD_DAYS}:\d+$")],
        states={BULK_DAYS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_add_days_execute)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), bulk_cancel)],
        per_message=False,
    )
    app.add_handler(bulk_days_conv)

    bulk_traffic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bulk_add_traffic_start, pattern=rf"^{CB_BULK_ADD_TRAFFIC}:\d+$")],
        states={BULK_TRAFFIC_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_add_traffic_execute)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), bulk_cancel)],
        per_message=False,
    )
    app.add_handler(bulk_traffic_conv)
