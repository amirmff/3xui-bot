"""Panel management handlers — add, remove, select, edit panels."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters,
)

import lang
from handlers.common import (
    admin_only, back_button, answer_and_edit, build_menu,
    CB_MAIN_MENU,
)
from panels import Panel

logger = logging.getLogger(__name__)

# Callback prefixes
CB_PANELS = "panels"
CB_PANEL_LIST = "pnl_list"
CB_PANEL_SELECT = "pnl_sel"
CB_PANEL_ADD = "pnl_add"
CB_PANEL_EDIT = "pnl_edit"
CB_PANEL_DEL = "pnl_del"
CB_PANEL_VIEW = "pnl_view"

# Conversation states
(ADD_NAME, ADD_URL, ADD_USER, ADD_PASS, ADD_PATH, ADD_PROXY, ADD_CONFIRM) = range(7)
(EDIT_SELECT, EDIT_VALUE) = range(10, 12)


def _get_panel_manager(context: ContextTypes.DEFAULT_TYPE):
    return context.bot_data["panel_manager"]


def _get_current_panel_id(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.bot_data.get("current_panel_id", "")


def _get_current_panel_name(context: ContextTypes.DEFAULT_TYPE) -> str:
    pm = _get_panel_manager(context)
    pid = _get_current_panel_id(context)
    panel = pm.get_panel(pid)
    return panel.name if panel else "—"


# ─── Panel Menu ───────────────────────────────────────────────

@admin_only
async def panels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show panel management menu."""
    pm = _get_panel_manager(context)
    current = _get_current_panel_name(context)
    count = pm.count()

    text = (
        f"🖥 <b>Panel Management</b>\n\n"
        f"📡 Active Panel: <b>{current}</b>\n"
        f"📋 Total Panels: <b>{count}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Panel List ({count})", callback_data=CB_PANEL_LIST)],
        [InlineKeyboardButton("➕ Add Panel", callback_data=CB_PANEL_ADD)],
        [back_button(CB_MAIN_MENU)],
    ])

    await answer_and_edit(update.callback_query, text, reply_markup=keyboard)


@admin_only
async def panels_menu_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """From reply keyboard."""
    pm = _get_panel_manager(context)
    current = _get_current_panel_name(context)
    count = pm.count()

    text = (
        f"🖥 <b>Panel Management</b>\n\n"
        f"📡 Active Panel: <b>{current}</b>\n"
        f"📋 Total Panels: <b>{count}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Panel List ({count})", callback_data=CB_PANEL_LIST)],
        [InlineKeyboardButton("➕ Add Panel", callback_data=CB_PANEL_ADD)],
        [back_button(CB_MAIN_MENU)],
    ])

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


# ─── Panel List & Select ──────────────────────────────────────

@admin_only
async def panel_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all panels."""
    query = update.callback_query
    await query.answer()

    pm = _get_panel_manager(context)
    panels = pm.get_all_panels()
    current_id = _get_current_panel_id(context)

    if not panels:
        await query.edit_message_text(
            "📋 <b>Panels</b>\n\nNo panels configured.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Panel", callback_data=CB_PANEL_ADD)],
                [back_button(CB_PANELS)],
            ]),
            parse_mode="HTML",
        )
        return

    buttons = []
    for p in panels:
        active = "🟢" if p.id == current_id else "⚪"
        label = f"{active} {p.name}"
        buttons.append(InlineKeyboardButton(label, callback_data=f"{CB_PANEL_VIEW}:{p.id}"))

    rows = build_menu(buttons, n_cols=1)
    rows.append([InlineKeyboardButton("➕ Add Panel", callback_data=CB_PANEL_ADD)])
    rows.append([back_button(CB_PANELS)])

    await query.edit_message_text(
        f"📋 <b>Panels ({len(panels)})</b>\n\n"
        f"🟢 = Active panel\n"
        f"Select a panel to manage or switch:",
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode="HTML",
    )


@admin_only
async def panel_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View panel details."""
    query = update.callback_query
    await query.answer()

    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return

    pm = _get_panel_manager(context)
    panel = pm.get_panel(panel_id)
    if not panel:
        await query.edit_message_text("❌ Panel not found.", parse_mode="HTML")
        return

    current_id = _get_current_panel_id(context)
    is_active = panel.id == current_id

    # Mask password
    masked_pass = panel.password[:2] + "***" if len(panel.password) > 2 else "***"

    text = (
        f"🖥 <b>Panel: {panel.name}</b>\n"
        f"{'🟢 Active' if is_active else '⚪ Inactive'}\n\n"
        f"<b>URL:</b> <code>{panel.url}</code>\n"
        f"<b>Username:</b> <code>{panel.username}</code>\n"
        f"<b>Password:</b> <code>{masked_pass}</code>\n"
        f"<b>Path:</b> <code>{panel.path or '—'}</code>\n"
        f"<b>Proxy:</b> <code>{panel.proxy_url or '—'}</code>"
    )

    buttons = []
    if not is_active:
        buttons.append([InlineKeyboardButton("🟢 Switch to This Panel", callback_data=f"{CB_PANEL_SELECT}:{panel_id}")])
    buttons.append([InlineKeyboardButton("🔌 Test Connection", callback_data=f"pnl_test:{panel_id}")])
    buttons.append([InlineKeyboardButton("✏️ Edit", callback_data=f"{CB_PANEL_EDIT}:{panel_id}")])
    buttons.append([InlineKeyboardButton("🗑 Delete", callback_data=f"{CB_PANEL_DEL}:{panel_id}")])
    buttons.append([back_button(CB_PANEL_LIST)])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


@admin_only
async def panel_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch active panel."""
    query = update.callback_query
    await query.answer()

    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return

    pm = _get_panel_manager(context)
    panel = pm.get_panel(panel_id)
    if not panel:
        await query.edit_message_text("❌ Panel not found.", parse_mode="HTML")
        return

    # Create new API client for this panel
    from api.client import XUIClient
    api = XUIClient(
        base_url=panel.api_base,
        username=panel.username,
        password=panel.password,
        proxy_url=panel.proxy_url,
    )

    # Try to login
    success = await api.login()
    if not success:
        # Close failed session
        await api.close()
        await query.edit_message_text(
            f"❌ <b>Failed to connect to {panel.name}</b>\n\n"
            f"Could not login. Check URL and credentials.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Edit Panel", callback_data=f"{CB_PANEL_EDIT}:{panel_id}")],
                [back_button(CB_PANEL_LIST)],
            ]),
            parse_mode="HTML",
        )
        return

    # Close old API client
    old_api = context.bot_data.get("api")
    if old_api:
        await old_api.close()

    # Set new active panel
    context.bot_data["api"] = api
    context.bot_data["current_panel_id"] = panel_id

    await query.edit_message_text(
        f"✅ <b>Switched to: {panel.name}</b>\n\n"
        f"URL: <code>{panel.url}</code>\n"
        f"Connected successfully!",
        reply_markup=InlineKeyboardMarkup([
            [back_button(CB_MAIN_MENU)],
        ]),
        parse_mode="HTML",
    )


# ─── Delete Panel ─────────────────────────────────────────────

@admin_only
async def panel_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return

    pm = _get_panel_manager(context)
    panel = pm.get_panel(panel_id)
    if not panel:
        return

    current_id = _get_current_panel_id(context)
    if panel_id == current_id:
        await query.edit_message_text(
            "⚠️ <b>Cannot delete the active panel!</b>\n\n"
            "Switch to another panel first.",
            reply_markup=InlineKeyboardMarkup([[back_button(CB_PANEL_LIST)]]),
            parse_mode="HTML",
        )
        return

    await query.edit_message_text(
        f"🗑 <b>Delete panel: {panel.name}?</b>\n\n"
        f"URL: <code>{panel.url}</code>\n\n"
        f"This action cannot be undone!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"pnl_del_yes:{panel_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"{CB_PANEL_VIEW}:{panel_id}"),
            ],
        ]),
        parse_mode="HTML",
    )


@admin_only
async def panel_delete_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return

    pm = _get_panel_manager(context)
    if pm.remove_panel(panel_id):
        text = "✅ Panel deleted."
    else:
        text = "❌ Panel not found."

    await query.edit_message_text(text,
        reply_markup=InlineKeyboardMarkup([[back_button(CB_PANEL_LIST)]]),
        parse_mode="HTML",
    )


# ─── Add Panel Conversation ──────────────────────────────────

@admin_only
async def add_panel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["new_panel"] = {}
    await query.edit_message_text(
        "➕ <b>Add New Panel</b>\n\n"
        "Step 1/6: Enter a <b>name</b> for this panel:\n\n"
        "<i>Example: Main Server, Iran Panel, Germany VPS</i>",
        parse_mode="HTML",
    )
    return ADD_NAME


@admin_only
async def add_panel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name or len(name) > 50:
        await update.message.reply_text("❌ Enter a valid name (max 50 chars).", parse_mode="HTML")
        return ADD_NAME

    context.user_data["new_panel"]["name"] = name
    await update.message.reply_text(
        f"✅ Name: <b>{name}</b>\n\n"
        "Step 2/6: Enter the <b>Panel URL</b>:\n\n"
        "<i>Example: https://your-server.com:2053</i>",
        parse_mode="HTML",
    )
    return ADD_URL


@admin_only
async def add_panel_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip().rstrip("/")
    if not url.startswith("http"):
        await update.message.reply_text("❌ URL must start with http:// or https://", parse_mode="HTML")
        return ADD_URL

    context.user_data["new_panel"]["url"] = url
    await update.message.reply_text(
        f"✅ URL: <b>{url}</b>\n\n"
        "Step 3/6: Enter <b>username</b>:\n\n"
        "<i>Default: admin</i>",
        parse_mode="HTML",
    )
    return ADD_USER


@admin_only
async def add_panel_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text.strip()
    if not username:
        username = "admin"

    context.user_data["new_panel"]["username"] = username
    await update.message.reply_text(
        f"✅ Username: <b>{username}</b>\n\n"
        "Step 4/6: Enter <b>password</b>:",
        parse_mode="HTML",
    )
    return ADD_PASS


@admin_only
async def add_panel_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    if not password:
        password = "admin"

    context.user_data["new_panel"]["password"] = password

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Skip (no path)", callback_data="pnl_skip_path")],
    ])
    await update.message.reply_text(
        "Step 5/6: Enter <b>panel path</b> (optional):\n\n"
        "<i>Leave empty or press Skip if default.\n"
        "Example: custom-path</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ADD_PATH


@admin_only
async def add_panel_path(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["new_panel"]["path"] = ""
    else:
        context.user_data["new_panel"]["path"] = update.message.text.strip().strip("/")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Skip (no proxy)", callback_data="pnl_skip_proxy")],
    ])

    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "Step 6/6: Enter <b>proxy URL</b> (optional):\n\n"
        "<i>Only needed if bot can't reach panel directly.\n"
        "Example: socks5://user:pass@ip:port</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ADD_PROXY


@admin_only
async def add_panel_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["new_panel"]["proxy_url"] = ""
        msg = update.callback_query.message
    else:
        context.user_data["new_panel"]["proxy_url"] = update.message.text.strip()
        msg = update.message

    data = context.user_data["new_panel"]
    proxy_str = data.get("proxy_url") or "none"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Add Panel", callback_data="pnl_add_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="pnl_add_cancel"),
        ],
    ])
    await msg.reply_text(
        f"📋 <b>Confirm New Panel</b>\n\n"
        f"<b>Name:</b> {data['name']}\n"
        f"<b>URL:</b> {data['url']}\n"
        f"<b>Username:</b> {data['username']}\n"
        f"<b>Password:</b> ***\n"
        f"<b>Path:</b> {data.get('path') or '—'}\n"
        f"<b>Proxy:</b> {proxy_str}\n\n"
        f"Add this panel?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ADD_CONFIRM


@admin_only
async def add_panel_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("new_panel", {})
    pm = _get_panel_manager(context)
    panel_id = pm.generate_id()

    panel = Panel(
        id=panel_id,
        name=data.get("name", ""),
        url=data.get("url", ""),
        username=data.get("username", "admin"),
        password=data.get("password", "admin"),
        path=data.get("path", ""),
        proxy_url=data.get("proxy_url", ""),
    )
    pm.add_panel(panel)

    # If this is the first panel, auto-select it
    if pm.count() == 1 or not context.bot_data.get("current_panel_id"):
        from api.client import XUIClient
        api = XUIClient(
            base_url=panel.api_base,
            username=panel.username,
            password=panel.password,
            proxy_url=panel.proxy_url,
        )
        success = await api.login()
        if success:
            old_api = context.bot_data.get("api")
            if old_api:
                await old_api.close()
            context.bot_data["api"] = api
            context.bot_data["current_panel_id"] = panel_id

    await query.edit_message_text(
        f"✅ <b>Panel added: {panel.name}</b>\n\n"
        f"Use 'Switch to This Panel' to activate it.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Switch Now", callback_data=f"{CB_PANEL_SELECT}:{panel_id}")],
            [back_button(CB_PANEL_LIST)],
        ]),
        parse_mode="HTML",
    )
    context.user_data.pop("new_panel", None)
    return ConversationHandler.END


async def add_panel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_panel", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Panel creation cancelled.",
            reply_markup=InlineKeyboardMarkup([[back_button(CB_PANELS)]]),
            parse_mode="HTML",
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Panel creation cancelled.",
            reply_markup=InlineKeyboardMarkup([[back_button(CB_PANELS)]]),
            parse_mode="HTML",
        )
    return ConversationHandler.END


# ─── Edit Panel Conversation ──────────────────────────────────

@admin_only
async def edit_panel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return ConversationHandler.END

    context.user_data["edit_panel_id"] = panel_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Name", callback_data="pedit:name")],
        [InlineKeyboardButton("🔗 URL", callback_data="pedit:url")],
        [InlineKeyboardButton("👤 Username", callback_data="pedit:username")],
        [InlineKeyboardButton("🔑 Password", callback_data="pedit:password")],
        [InlineKeyboardButton("📂 Path", callback_data="pedit:path")],
        [InlineKeyboardButton("🔌 Proxy", callback_data="pedit:proxy_url")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pedit_cancel")],
    ])
    await query.edit_message_text(
        "✏️ <b>Edit Panel</b>\n\nSelect what to change:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return EDIT_SELECT


@admin_only
async def edit_panel_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    field = query.data.split(":")[1]
    context.user_data["edit_panel_field"] = field

    field_labels = {
        "name": "name",
        "url": "URL",
        "username": "username",
        "password": "password",
        "path": "path (empty for none)",
        "proxy_url": "proxy URL (empty for none)",
    }

    await query.edit_message_text(
        f"✏️ Enter new <b>{field_labels.get(field, field)}</b>:",
        parse_mode="HTML",
    )
    return EDIT_VALUE


@admin_only
async def edit_panel_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    panel_id = context.user_data.get("edit_panel_id")
    field = context.user_data.get("edit_panel_field")

    pm = _get_panel_manager(context)
    panel = pm.get_panel(panel_id)
    if not panel:
        await update.message.reply_text("❌ Panel not found.", parse_mode="HTML")
        return ConversationHandler.END

    # Update field
    if field == "url":
        value = value.rstrip("/")
        if not value.startswith("http"):
            await update.message.reply_text("❌ URL must start with http:// or https://", parse_mode="HTML")
            return EDIT_VALUE
    setattr(panel, field, value)
    pm.add_panel(panel)  # Save

    # If editing active panel, reconnect
    current_id = _get_current_panel_id(context)
    if panel_id == current_id:
        from api.client import XUIClient
        old_api = context.bot_data.get("api")
        if old_api:
            await old_api.close()
        api = XUIClient(
            base_url=panel.api_base,
            username=panel.username,
            password=panel.password,
            proxy_url=panel.proxy_url,
        )
        await api.login()
        context.bot_data["api"] = api

    await update.message.reply_text(
        f"✅ Panel <b>{panel.name}</b> updated!\n\n"
        f"<b>{field}</b> → <code>{value if field != 'password' else '***'}</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 View", callback_data=f"{CB_PANEL_VIEW}:{panel_id}")],
            [back_button(CB_PANEL_LIST)],
        ]),
        parse_mode="HTML",
    )
    context.user_data.pop("edit_panel_id", None)
    context.user_data.pop("edit_panel_field", None)
    return ConversationHandler.END


async def edit_panel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("edit_panel_id", None)
    context.user_data.pop("edit_panel_field", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Edit cancelled.",
            reply_markup=InlineKeyboardMarkup([[back_button(CB_PANEL_LIST)]]),
            parse_mode="HTML",
        )
    return ConversationHandler.END


# ─── Test Connection ──────────────────────────────────────────

@admin_only
async def panel_test_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test connection to a panel."""
    query = update.callback_query
    await query.answer()

    try:
        panel_id = query.data.split(":")[1]
    except (IndexError,):
        return

    pm = _get_panel_manager(context)
    panel = pm.get_panel(panel_id)
    if not panel:
        await query.edit_message_text("❌ Panel not found.", parse_mode="HTML")
        return

    await query.edit_message_text(
        f"🔌 <b>Testing: {panel.name}</b>\n\n⏳ Connecting...",
        parse_mode="HTML",
    )

    from api.client import XUIClient
    test_api = XUIClient(
        base_url=panel.api_base,
        username=panel.username,
        password=panel.password,
        proxy_url=panel.proxy_url,
    )

    try:
        success = await test_api.login()
        await test_api.close()

        if success:
            text = (
                f"🔌 <b>Test: {panel.name}</b>\n\n"
                f"✅ <b>Connection: OK</b>\n"
                f"✅ <b>Login: OK</b>\n\n"
                f"URL: <code>{panel.url}</code>\n"
                f"Proxy: <code>{panel.proxy_url or 'none'}</code>"
            )
        else:
            text = (
                f"🔌 <b>Test: {panel.name}</b>\n\n"
                f"⚠️ <b>Connection: OK</b>\n"
                f"❌ <b>Login: FAILED</b>\n\n"
                f"Check username/password."
            )
    except Exception as e:
        await test_api.close()
        text = (
            f"🔌 <b>Test: {panel.name}</b>\n\n"
            f"❌ <b>Connection: FAILED</b>\n\n"
            f"Error: <code>{str(e)[:200]}</code>"
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Retry", callback_data=f"pnl_test:{panel_id}")],
            [back_button(f"{CB_PANEL_VIEW}:{panel_id}")],
        ]),
        parse_mode="HTML",
    )


# ─── Register ─────────────────────────────────────────────────

def register(app) -> None:
    """Register panel management handlers."""
    app.add_handler(CallbackQueryHandler(panels_menu, pattern=f"^{CB_PANELS}$"))
    app.add_handler(CallbackQueryHandler(panel_list, pattern=f"^{CB_PANEL_LIST}$"))
    app.add_handler(CallbackQueryHandler(panel_view, pattern=rf"^{CB_PANEL_VIEW}:"))
    app.add_handler(CallbackQueryHandler(panel_select, pattern=rf"^{CB_PANEL_SELECT}:"))
    app.add_handler(CallbackQueryHandler(panel_delete_confirm, pattern=rf"^{CB_PANEL_DEL}:"))
    app.add_handler(CallbackQueryHandler(panel_delete_execute, pattern=r"^pnl_del_yes:"))
    app.add_handler(CallbackQueryHandler(panel_test_connection, pattern=r"^pnl_test:"))

    # Add panel conversation
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_panel_start, pattern=f"^{CB_PANEL_ADD}$")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_name)],
            ADD_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_url)],
            ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_username)],
            ADD_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_password)],
            ADD_PATH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_path),
                CallbackQueryHandler(add_panel_path, pattern=r"^pnl_skip_path$"),
            ],
            ADD_PROXY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_panel_proxy),
                CallbackQueryHandler(add_panel_proxy, pattern=r"^pnl_skip_proxy$"),
            ],
            ADD_CONFIRM: [
                CallbackQueryHandler(add_panel_execute, pattern=r"^pnl_add_confirm$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(add_panel_cancel, pattern=r"^pnl_add_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), add_panel_cancel),
        ],
        per_message=False,
    )
    app.add_handler(add_conv)

    # Edit panel conversation
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_panel_start, pattern=rf"^{CB_PANEL_EDIT}:")],
        states={
            EDIT_SELECT: [CallbackQueryHandler(edit_panel_select, pattern=r"^pedit:")],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_panel_value)],
        },
        fallbacks=[
            CallbackQueryHandler(edit_panel_cancel, pattern=r"^pedit_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), edit_panel_cancel),
        ],
        per_message=False,
    )
    app.add_handler(edit_conv)
