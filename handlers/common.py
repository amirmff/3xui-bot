"""Common utilities, decorators, and keyboard builders for handlers."""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Sequence

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, Update,
)
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_IDS
import lang

logger = logging.getLogger(__name__)

# ─── Callback data prefixes ──────────────────────────────────────────────────

# Main menu
CB_MAIN_MENU = "main_menu"
CB_INBOUNDS = "inbounds"
CB_CLIENTS = "clients"
CB_SERVER = "server"
CB_BACKUP = "backup"
CB_ONLINE = "online"
CB_PANELS = "panels"
CB_HELP = "help"
CB_STATUS = "status"

# Inbound actions
CB_INBOUND_LIST = "inb_list"
CB_INBOUND_VIEW = "inb_view"
CB_INBOUND_ADD = "inb_add"
CB_INBOUND_EDIT = "inb_edit"
CB_INBOUND_DEL = "inb_del"
CB_INBOUND_TOGGLE = "inb_toggle"
CB_INBOUND_CLIENTS = "inb_clients"

# Client actions
CB_CLIENT_LIST = "cl_list"
CB_CLIENT_VIEW = "cl_view"
CB_CLIENT_ADD = "cl_add"
CB_CLIENT_EDIT = "cl_edit"
CB_CLIENT_DEL = "cl_del"
CB_CLIENT_LINK = "cl_link"
CB_CLIENT_QR = "cl_qr"
CB_CLIENT_TRAFFIC = "cl_traffic"
CB_CLIENT_RESET_TRAFFIC = "cl_reset_tr"
CB_CLIENT_TOGGLE = "cl_toggle"
CB_CLIENT_IPS = "cl_ips"
CB_CLIENT_CLEAR_IPS = "cl_clear_ips"

# New client actions
CB_CLIENT_ADD_DAYS = "cl_add_days"
CB_CLIENT_ADD_TRAFFIC = "cl_add_vol"
CB_CLIENT_RENEW = "cl_renew"
CB_QUICK_TEMPLATE = "cl_quick"

# Bulk actions
CB_BULK_RESET_ALL = "bulk_reset_all"
CB_BULK_RESET_INB = "bulk_reset_inb"
CB_BULK_DEL_DEPLETED = "bulk_del_dep"
CB_BULK_ADD_DAYS = "bulk_add_days"
CB_BULK_ADD_TRAFFIC = "bulk_add_vol"

# Server actions
CB_SERVER_STATUS = "srv_status"
CB_SERVER_RESTART_XRAY = "srv_restart"
CB_SERVER_STOP_XRAY = "srv_stop"
CB_SERVER_XRAY_VER = "srv_xray_ver"
CB_SERVER_INSTALL_XRAY = "srv_install"
CB_SERVER_UPDATE_GEO = "srv_geo"
CB_SERVER_LOGS = "srv_logs"
CB_SERVER_XRAY_LOGS = "srv_xlogs"
CB_SERVER_NEW_UUID = "srv_uuid"
CB_SERVER_NEW_X25519 = "srv_x25519"
CB_SERVER_CONFIG = "srv_config"

# Backup actions
CB_BACKUP_DB = "bak_db"
CB_BACKUP_CONFIG = "bak_config"
CB_BACKUP_IMPORT = "bak_import"
CB_BACKUP_TG = "bak_tg"

# Pagination
CB_PAGE = "page"

# Confirmation
CB_CONFIRM_YES = "confirm_yes"
CB_CONFIRM_NO = "confirm_no"


# ─── API client accessor ─────────────────────────────────────────────────────

def get_api(context: ContextTypes.DEFAULT_TYPE):
    """Get the XUI API client from bot_data."""
    return context.bot_data["api"]


# ─── Admin-only decorator ────────────────────────────────────────────────────

def admin_only(func: Callable) -> Callable:
    """Decorator that restricts handler to admin users only."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any):
        user_id = None
        if update.effective_user:
            user_id = update.effective_user.id
        if user_id not in ADMIN_CHAT_IDS:
            if update.callback_query:
                await update.callback_query.answer(lang.ACCESS_DENIED, show_alert=True)
            elif update.message:
                await update.message.reply_text(lang.ACCESS_DENIED)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


# ─── Reply Keyboard (persistent bottom keyboard) ─────────────────────────────

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Build the persistent reply keyboard (glass buttons)."""
    keyboard = [
        [KeyboardButton(lang.BTN_INBOUNDS), KeyboardButton(lang.BTN_CLIENTS)],
        [KeyboardButton(lang.BTN_SERVER), KeyboardButton(lang.BTN_BACKUP)],
        [KeyboardButton(lang.BTN_ONLINE), KeyboardButton(lang.BTN_STATUS)],
        [KeyboardButton(lang.BTN_PANELS)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


# ─── Inline Keyboard builders ────────────────────────────────────────────────

def build_menu(
    buttons: list[InlineKeyboardButton],
    n_cols: int = 2,
    header_buttons: list[InlineKeyboardButton] | None = None,
    footer_buttons: list[InlineKeyboardButton] | None = None,
) -> list[list[InlineKeyboardButton]]:
    """Arrange buttons into a grid layout."""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def main_menu_keyboard(context=None) -> InlineKeyboardMarkup:
    """Build the main menu inline keyboard with current panel indicator."""
    # Current panel name
    panel_label = "🖥 Panels"
    if context and context.bot_data.get("panel_manager"):
        pm = context.bot_data["panel_manager"]
        pid = context.bot_data.get("current_panel_id", "")
        panel = pm.get_panel(pid)
        if panel:
            panel_label = f"🖥 {panel.name}"

    buttons = [
        [
            InlineKeyboardButton(lang.BTN_INBOUNDS, callback_data=CB_INBOUNDS),
            InlineKeyboardButton(lang.BTN_CLIENTS, callback_data=CB_CLIENTS),
        ],
        [
            InlineKeyboardButton(lang.BTN_SERVER, callback_data=CB_SERVER),
            InlineKeyboardButton(lang.BTN_BACKUP, callback_data=CB_BACKUP),
        ],
        [
            InlineKeyboardButton(lang.BTN_ONLINE, callback_data=CB_ONLINE),
            InlineKeyboardButton(panel_label, callback_data=CB_PANELS),
        ],
        [
            InlineKeyboardButton(lang.BTN_HELP, callback_data=CB_HELP),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def back_button(callback_data: str = CB_MAIN_MENU) -> InlineKeyboardButton:
    """Create a back button."""
    return InlineKeyboardButton(lang.BTN_BACK, callback_data=callback_data)


def confirm_keyboard(
    yes_data: str = CB_CONFIRM_YES,
    no_data: str = CB_CONFIRM_NO,
) -> InlineKeyboardMarkup:
    """Build a Yes/No confirmation keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data=yes_data),
            InlineKeyboardButton(lang.BTN_CONFIRM_NO, callback_data=no_data),
        ]
    ])


def paginate_buttons(
    items: Sequence[tuple[str, str]],
    page: int = 0,
    per_page: int = 8,
    n_cols: int = 1,
    back_cb: str = CB_MAIN_MENU,
    page_prefix: str = CB_PAGE,
) -> InlineKeyboardMarkup:
    """Build a paginated inline keyboard from (label, callback_data) tuples."""
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))

    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    # Item buttons
    buttons = [InlineKeyboardButton(label, callback_data=cb) for label, cb in page_items]
    rows = build_menu(buttons, n_cols=n_cols)

    # Navigation row
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"{page_prefix}:{page - 1}"))
    nav.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"{page_prefix}:{page + 1}"))

    if nav:
        rows.append(nav)

    # Back button
    rows.append([back_button(back_cb)])

    return InlineKeyboardMarkup(rows)


# ─── Response helpers ─────────────────────────────────────────────────────────

async def answer_and_edit(
    query,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
) -> None:
    """Answer callback query and edit message text."""
    await query.answer()
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.error("Error editing message: %s", e)


async def send_or_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
) -> None:
    """Send a new message or edit existing one depending on update type."""
    if update.callback_query:
        await answer_and_edit(update.callback_query, text, reply_markup, parse_mode)
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
