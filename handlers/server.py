"""Server management handlers — Persian UI."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

import lang
from handlers.common import (
    admin_only, get_api, back_button, answer_and_edit, build_menu,
    CB_SERVER, CB_SERVER_STATUS, CB_SERVER_RESTART_XRAY, CB_SERVER_STOP_XRAY,
    CB_SERVER_XRAY_VER, CB_SERVER_INSTALL_XRAY, CB_SERVER_UPDATE_GEO,
    CB_SERVER_LOGS, CB_SERVER_XRAY_LOGS, CB_SERVER_NEW_UUID, CB_SERVER_NEW_X25519,
    CB_MAIN_MENU,
)
from utils.formatters import format_server_status

logger = logging.getLogger(__name__)


@admin_only
async def server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.SRV_STATUS, callback_data=CB_SERVER_STATUS),
            InlineKeyboardButton(lang.SRV_RESTART_XRAY, callback_data=CB_SERVER_RESTART_XRAY),
        ],
        [
            InlineKeyboardButton(lang.SRV_STOP_XRAY, callback_data=CB_SERVER_STOP_XRAY),
            InlineKeyboardButton(lang.SRV_XRAY_VER, callback_data=CB_SERVER_XRAY_VER),
        ],
        [InlineKeyboardButton(lang.SRV_UPDATE_GEO, callback_data=CB_SERVER_UPDATE_GEO)],
        [
            InlineKeyboardButton(lang.SRV_SYS_LOGS, callback_data=f"{CB_SERVER_LOGS}:50"),
            InlineKeyboardButton(lang.SRV_XRAY_LOGS, callback_data=f"{CB_SERVER_XRAY_LOGS}:50"),
        ],
        [
            InlineKeyboardButton(lang.SRV_NEW_UUID, callback_data=CB_SERVER_NEW_UUID),
            InlineKeyboardButton(lang.SRV_NEW_X25519, callback_data=CB_SERVER_NEW_X25519),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await answer_and_edit(update.callback_query, lang.SRV_MANAGEMENT, reply_markup=keyboard)


@admin_only
async def server_menu_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show server menu from reply keyboard."""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.SRV_STATUS, callback_data=CB_SERVER_STATUS),
            InlineKeyboardButton(lang.SRV_RESTART_XRAY, callback_data=CB_SERVER_RESTART_XRAY),
        ],
        [
            InlineKeyboardButton(lang.SRV_STOP_XRAY, callback_data=CB_SERVER_STOP_XRAY),
            InlineKeyboardButton(lang.SRV_XRAY_VER, callback_data=CB_SERVER_XRAY_VER),
        ],
        [InlineKeyboardButton(lang.SRV_UPDATE_GEO, callback_data=CB_SERVER_UPDATE_GEO)],
        [
            InlineKeyboardButton(lang.SRV_SYS_LOGS, callback_data=f"{CB_SERVER_LOGS}:50"),
            InlineKeyboardButton(lang.SRV_XRAY_LOGS, callback_data=f"{CB_SERVER_XRAY_LOGS}:50"),
        ],
        [
            InlineKeyboardButton(lang.SRV_NEW_UUID, callback_data=CB_SERVER_NEW_UUID),
            InlineKeyboardButton(lang.SRV_NEW_X25519, callback_data=CB_SERVER_NEW_X25519),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await update.message.reply_text(lang.SRV_MANAGEMENT, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    try:
        result = await api.get_server_status()
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")
            return
        text = format_server_status(result)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=CB_SERVER_STATUS)],
            [back_button(CB_SERVER)],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e),
                                      reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def restart_xray_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data="srv_restart_yes"),
            InlineKeyboardButton(lang.BTN_CANCEL, callback_data=CB_SERVER),
        ],
    ])
    await query.edit_message_text(lang.SRV_RESTART_CONFIRM, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def restart_xray_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال ریستارت...")
    api = get_api(context)
    try:
        result = await api.restart_xray()
        text = lang.SRV_RESTART_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def stop_xray_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data="srv_stop_yes"),
            InlineKeyboardButton(lang.BTN_CANCEL, callback_data=CB_SERVER),
        ],
    ])
    await query.edit_message_text(lang.SRV_STOP_CONFIRM, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def stop_xray_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال توقف...")
    api = get_api(context)
    try:
        result = await api.stop_xray()
        text = lang.SRV_STOP_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def xray_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    try:
        result = await api.get_xray_version()
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")
            return

        versions = result.get("obj", [])
        if isinstance(versions, list) and versions:
            buttons = []
            for v in versions[:10]:
                ver = v if isinstance(v, str) else str(v)
                buttons.append(InlineKeyboardButton(f"📥 {ver}", callback_data=f"{CB_SERVER_INSTALL_XRAY}:{ver}"))
            rows = build_menu(buttons, n_cols=2)
            rows.append([back_button(CB_SERVER)])
            await query.edit_message_text(lang.SRV_VERSIONS_TITLE, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
        else:
            await query.edit_message_text(
                f"📋 <b>نسخه Xray</b>\n\n<pre>{result.get('obj', 'N/A')}</pre>",
                reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


@admin_only
async def install_xray_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    version = query.data.split(":")[1]
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BTN_CONFIRM_YES, callback_data=f"srv_install_yes:{version}"),
            InlineKeyboardButton(lang.BTN_CANCEL, callback_data=CB_SERVER),
        ],
    ])
    await query.edit_message_text(lang.SRV_INSTALL_CONFIRM.format(version=version), reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def install_xray_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    version = query.data.split(":")[1]
    await query.answer(f"در حال نصب {version}...")
    api = get_api(context)
    try:
        result = await api.install_xray(version)
        text = lang.SRV_INSTALL_SUCCESS.format(version=version) if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def update_geofiles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال آپدیت...")
    api = get_api(context)
    try:
        result = await api.update_geofiles()
        text = lang.SRV_GEO_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def system_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        count = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        count = 50

    api = get_api(context)
    try:
        result = await api.get_logs(count)
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")
            return

        logs = result.get("obj", "")
        if isinstance(logs, list):
            logs = "\n".join(str(l) for l in logs)
        logs = str(logs)
        if len(logs) > 3800:
            logs = logs[-3800:]
            logs = "...(truncated)\n" + logs

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📜 ۱۰ آخر", callback_data=f"{CB_SERVER_LOGS}:10"),
                InlineKeyboardButton("📜 ۵۰ آخر", callback_data=f"{CB_SERVER_LOGS}:50"),
                InlineKeyboardButton("📜 ۱۰۰ آخر", callback_data=f"{CB_SERVER_LOGS}:100"),
            ],
            [back_button(CB_SERVER)],
        ])
        await query.edit_message_text(
            lang.SRV_LOGS_TITLE.format(type="سیستم", count=count) + f"\n\n<pre>{logs}</pre>",
            reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e),
                                      reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def xray_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        count = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        count = 50

    api = get_api(context)
    try:
        result = await api.get_xray_logs(count)
        if not result.get("success"):
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")
            return

        logs = result.get("obj", "")
        if isinstance(logs, list):
            logs = "\n".join(str(l) for l in logs)
        logs = str(logs)
        if len(logs) > 3800:
            logs = logs[-3800:]
            logs = "...(truncated)\n" + logs

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📜 ۱۰ آخر", callback_data=f"{CB_SERVER_XRAY_LOGS}:10"),
                InlineKeyboardButton("📜 ۵۰ آخر", callback_data=f"{CB_SERVER_XRAY_LOGS}:50"),
                InlineKeyboardButton("📜 ۱۰۰ آخر", callback_data=f"{CB_SERVER_XRAY_LOGS}:100"),
            ],
            [back_button(CB_SERVER)],
        ])
        await query.edit_message_text(
            lang.SRV_LOGS_TITLE.format(type="Xray", count=count) + f"\n\n<pre>{logs}</pre>",
            reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e),
                                      reply_markup=InlineKeyboardMarkup([[back_button(CB_SERVER)]]), parse_mode="HTML")


@admin_only
async def new_uuid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    try:
        result = await api.get_new_uuid()
        if result.get("success"):
            text = f"{lang.SRV_UUID_TITLE}\n\n<code>{result.get('obj', 'N/A')}</code>"
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.SRV_UUID_ANOTHER, callback_data=CB_SERVER_NEW_UUID)],
        [back_button(CB_SERVER)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def new_x25519(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    api = get_api(context)
    try:
        result = await api.get_new_x25519()
        if result.get("success"):
            obj = result.get("obj", {})
            if isinstance(obj, dict):
                private = obj.get("privateKey", "N/A")
                public = obj.get("publicKey", "N/A")
            else:
                private = str(obj)
                public = ""
            text = (f"{lang.SRV_X25519_TITLE}\n\n"
                    f"<b>کلید خصوصی:</b>\n<code>{private}</code>\n\n"
                    f"<b>کلید عمومی:</b>\n<code>{public}</code>")
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 تولید دوباره", callback_data=CB_SERVER_NEW_X25519)],
        [back_button(CB_SERVER)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


def register(app) -> None:
    app.add_handler(CallbackQueryHandler(server_menu, pattern=f"^{CB_SERVER}$"))
    app.add_handler(CallbackQueryHandler(server_status, pattern=f"^{CB_SERVER_STATUS}$"))
    app.add_handler(CallbackQueryHandler(restart_xray_confirm, pattern=f"^{CB_SERVER_RESTART_XRAY}$"))
    app.add_handler(CallbackQueryHandler(restart_xray_execute, pattern=r"^srv_restart_yes$"))
    app.add_handler(CallbackQueryHandler(stop_xray_confirm, pattern=f"^{CB_SERVER_STOP_XRAY}$"))
    app.add_handler(CallbackQueryHandler(stop_xray_execute, pattern=r"^srv_stop_yes$"))
    app.add_handler(CallbackQueryHandler(xray_version, pattern=f"^{CB_SERVER_XRAY_VER}$"))
    app.add_handler(CallbackQueryHandler(install_xray_confirm, pattern=rf"^{CB_SERVER_INSTALL_XRAY}:"))
    app.add_handler(CallbackQueryHandler(install_xray_execute, pattern=r"^srv_install_yes:"))
    app.add_handler(CallbackQueryHandler(update_geofiles, pattern=f"^{CB_SERVER_UPDATE_GEO}$"))
    app.add_handler(CallbackQueryHandler(system_logs, pattern=rf"^{CB_SERVER_LOGS}:\d+$"))
    app.add_handler(CallbackQueryHandler(xray_logs, pattern=rf"^{CB_SERVER_XRAY_LOGS}:\d+$"))
    app.add_handler(CallbackQueryHandler(new_uuid, pattern=f"^{CB_SERVER_NEW_UUID}$"))
    app.add_handler(CallbackQueryHandler(new_x25519, pattern=f"^{CB_SERVER_NEW_X25519}$"))
