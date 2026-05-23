"""Backup and restore handlers — Persian UI."""

from __future__ import annotations

import io
import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters,
)

import lang
from handlers.common import (
    admin_only, get_api, back_button, answer_and_edit,
    CB_BACKUP, CB_BACKUP_DB, CB_BACKUP_CONFIG, CB_BACKUP_IMPORT, CB_BACKUP_TG,
    CB_MAIN_MENU,
)

logger = logging.getLogger(__name__)
WAITING_FILE = 0


@admin_only
async def backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BAK_DOWNLOAD_DB, callback_data=CB_BACKUP_DB),
            InlineKeyboardButton(lang.BAK_DOWNLOAD_CONFIG, callback_data=CB_BACKUP_CONFIG),
        ],
        [
            InlineKeyboardButton(lang.BAK_IMPORT_DB, callback_data=CB_BACKUP_IMPORT),
            InlineKeyboardButton(lang.BAK_BACKUP_TG, callback_data=CB_BACKUP_TG),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await answer_and_edit(update.callback_query, lang.BAK_MANAGEMENT, reply_markup=keyboard)


@admin_only
async def backup_menu_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show backup menu from reply keyboard."""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BAK_DOWNLOAD_DB, callback_data=CB_BACKUP_DB),
            InlineKeyboardButton(lang.BAK_DOWNLOAD_CONFIG, callback_data=CB_BACKUP_CONFIG),
        ],
        [
            InlineKeyboardButton(lang.BAK_IMPORT_DB, callback_data=CB_BACKUP_IMPORT),
            InlineKeyboardButton(lang.BAK_BACKUP_TG, callback_data=CB_BACKUP_TG),
        ],
        [back_button(CB_MAIN_MENU)],
    ])
    await update.message.reply_text(lang.BAK_MANAGEMENT, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال دانلود...")
    api = get_api(context)
    try:
        db_bytes = await api.get_db()
        if db_bytes:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(io.BytesIO(db_bytes), filename="x-ui.db"),
                caption=lang.BAK_DB_CAPTION, parse_mode="HTML",
            )
        else:
            await query.edit_message_text(lang.FAILED.format(msg="پاسخ خالی"),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e),
                                      reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")


@admin_only
async def download_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال دانلود...")
    api = get_api(context)
    try:
        result = await api.get_config_json()
        if result.get("success"):
            config_data = result.get("obj", {})
            config_str = json.dumps(config_data, indent=2, ensure_ascii=False)
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(io.BytesIO(config_str.encode("utf-8")), filename="config.json"),
                caption=lang.BAK_CONFIG_CAPTION, parse_mode="HTML",
            )
        else:
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")),
                                          reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e),
                                      reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")


@admin_only
async def import_db_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(lang.BAK_IMPORT_PROMPT, parse_mode="HTML")
    return WAITING_FILE


@admin_only
async def import_db_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return WAITING_FILE
    if not document.file_name.endswith(".db"):
        await update.message.reply_text("❌ لطفاً فایل <code>.db</code> ارسال کنید.", parse_mode="HTML")
        return WAITING_FILE

    await update.message.reply_text("⏳ در حال ایمپورت...")
    api = get_api(context)
    try:
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await api.import_db(bytes(file_bytes))
        if result.get("success"):
            text = lang.BAK_IMPORT_SUCCESS
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")
    return ConversationHandler.END


async def import_db_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(lang.OPERATION_CANCELLED,
                                     reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")
    return ConversationHandler.END


@admin_only
async def backup_to_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("در حال ارسال بکاپ...")
    api = get_api(context)
    try:
        result = await api.backup_to_telegram()
        text = lang.BAK_TG_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button(CB_BACKUP)]]), parse_mode="HTML")


def register(app) -> None:
    app.add_handler(CallbackQueryHandler(backup_menu, pattern=f"^{CB_BACKUP}$"))
    app.add_handler(CallbackQueryHandler(download_db, pattern=f"^{CB_BACKUP_DB}$"))
    app.add_handler(CallbackQueryHandler(download_config, pattern=f"^{CB_BACKUP_CONFIG}$"))
    app.add_handler(CallbackQueryHandler(backup_to_telegram, pattern=f"^{CB_BACKUP_TG}$"))

    import_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(import_db_start, pattern=f"^{CB_BACKUP_IMPORT}$")],
        states={WAITING_FILE: [MessageHandler(filters.Document.ALL, import_db_receive)]},
        fallbacks=[MessageHandler(filters.Regex(r"^/cancel$"), import_db_cancel)],
        per_message=False,
    )
    app.add_handler(import_conv)
