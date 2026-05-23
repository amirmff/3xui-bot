"""Start, main menu, help, and online users handlers with reply keyboard."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import lang
from handlers.common import (
    admin_only, get_api, main_menu_keyboard, main_reply_keyboard,
    send_or_edit, answer_and_edit, back_button,
    CB_MAIN_MENU, CB_HELP, CB_ONLINE, CB_STATUS, CB_PANELS,
    CB_INBOUNDS, CB_CLIENTS, CB_SERVER, CB_BACKUP,
)
from utils.formatters import format_online_clients, format_server_status

logger = logging.getLogger(__name__)


@admin_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — show main menu + reply keyboard."""
    # Get active panel name
    pm = context.bot_data.get("panel_manager")
    pid = context.bot_data.get("current_panel_id", "")
    panel_name = "—"
    if pm:
        panel = pm.get_panel(pid)
        if panel:
            panel_name = panel.name

    # Send reply keyboard first
    await update.message.reply_text(
        "⌨️",
        reply_markup=main_reply_keyboard(),
    )
    # Then send inline menu
    await update.message.reply_text(
        lang.WELCOME + f"\n\n📡 <b>پنل فعال:</b> {panel_name}",
        reply_markup=main_menu_keyboard(context),
        parse_mode="HTML",
    )


@admin_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    keyboard = InlineKeyboardMarkup([[back_button(CB_MAIN_MENU)]])
    await send_or_edit(update, context, lang.HELP, reply_markup=keyboard)


@admin_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command — quick server status."""
    api = get_api(context)
    try:
        result = await api.get_server_status()
        if result.get("success"):
            text = format_server_status(result)
        else:
            text = lang.FAILED.format(msg=result.get("msg", "Unknown"))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=CB_STATUS)],
        [back_button(CB_MAIN_MENU)],
    ])
    await send_or_edit(update, context, text, reply_markup=keyboard)


@admin_only
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu callback."""
    pm = context.bot_data.get("panel_manager")
    pid = context.bot_data.get("current_panel_id", "")
    panel_name = "—"
    if pm:
        panel = pm.get_panel(pid)
        if panel:
            panel_name = panel.name
    await answer_and_edit(
        update.callback_query,
        lang.WELCOME + f"\n\n📡 <b>پنل فعال:</b> {panel_name}",
        reply_markup=main_menu_keyboard(context),
    )


@admin_only
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help callback."""
    keyboard = InlineKeyboardMarkup([[back_button(CB_MAIN_MENU)]])
    await answer_and_edit(update.callback_query, lang.HELP, reply_markup=keyboard)


@admin_only
async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle status callback from inline button."""
    query = update.callback_query
    await query.answer()

    api = get_api(context)
    try:
        result = await api.get_server_status()
        if result.get("success"):
            text = format_server_status(result)
        else:
            text = lang.FAILED.format(msg=result.get("msg", "Unknown"))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=CB_STATUS)],
        [back_button(CB_MAIN_MENU)],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def online_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show currently online clients."""
    query = update.callback_query
    await query.answer()

    api = get_api(context)
    try:
        result = await api.get_online_clients()
        if result.get("success"):
            emails = result.get("obj", [])
            if emails is None:
                emails = []
            text = format_online_clients(emails)
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        logger.error("Error getting online clients: %s", e)
        text = lang.ERROR.format(error=e)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=CB_ONLINE)],
        [back_button(CB_MAIN_MENU)],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle no-op callbacks."""
    if update.callback_query:
        await update.callback_query.answer()


# ─── Reply Keyboard Text Handlers ─────────────────────────────────────────────

@admin_only
async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from reply keyboard buttons."""
    text = update.message.text

    if text == lang.BTN_INBOUNDS:
        from handlers.inbounds import inbounds_menu_msg
        await inbounds_menu_msg(update, context)
    elif text == lang.BTN_CLIENTS:
        from handlers.clients import clients_menu_msg
        await clients_menu_msg(update, context)
    elif text == lang.BTN_SERVER:
        from handlers.server import server_menu_msg
        await server_menu_msg(update, context)
    elif text == lang.BTN_BACKUP:
        from handlers.backup import backup_menu_msg
        await backup_menu_msg(update, context)
    elif text == lang.BTN_ONLINE:
        api = get_api(context)
        try:
            result = await api.get_online_clients()
            if result.get("success"):
                emails = result.get("obj") or []
                msg = format_online_clients(emails)
            else:
                msg = lang.FAILED.format(msg=result.get("msg", ""))
        except Exception as e:
            msg = lang.ERROR.format(error=e)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=CB_ONLINE)],
        ])
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="HTML")
    elif text == lang.BTN_STATUS:
        await status_command(update, context)
    elif text == lang.BTN_PANELS:
        from handlers.panels import panels_menu_msg
        await panels_menu_msg(update, context)
    else:
        # Unknown text, show menu
        await update.message.reply_text(
            lang.WELCOME,
            reply_markup=main_menu_keyboard(context),
            parse_mode="HTML",
        )


def register(app) -> None:
    """Register start/menu/help handlers."""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern=f"^{CB_MAIN_MENU}$"))
    app.add_handler(CallbackQueryHandler(help_callback, pattern=f"^{CB_HELP}$"))
    app.add_handler(CallbackQueryHandler(online_callback, pattern=f"^{CB_ONLINE}$"))
    app.add_handler(CallbackQueryHandler(status_callback, pattern=f"^{CB_STATUS}$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))

    # Reply keyboard handler — must be added LAST (low priority)
    reply_filter = filters.TEXT & ~filters.COMMAND & filters.Regex(
        f"^({lang.BTN_INBOUNDS}|{lang.BTN_CLIENTS}|{lang.BTN_SERVER}|"
        f"{lang.BTN_BACKUP}|{lang.BTN_ONLINE}|{lang.BTN_STATUS}|{lang.BTN_PANELS})$"
    )
    app.add_handler(MessageHandler(reply_filter, reply_keyboard_handler), group=1)
