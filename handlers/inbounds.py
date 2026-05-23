"""Inbound management handlers — Persian UI."""

from __future__ import annotations

import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters,
)

import lang
from handlers.common import (
    admin_only, get_api, back_button, answer_and_edit, send_or_edit,
    paginate_buttons, build_menu,
    CB_INBOUNDS, CB_INBOUND_LIST, CB_INBOUND_VIEW, CB_INBOUND_ADD,
    CB_INBOUND_DEL, CB_INBOUND_TOGGLE, CB_INBOUND_CLIENTS, CB_MAIN_MENU,
)
from utils.formatters import format_inbound_detail
from utils.helpers import generate_uuid, generate_password, generate_sub_id

logger = logging.getLogger(__name__)

ASK_PROTOCOL, ASK_REMARK, ASK_PORT, ASK_NETWORK, ASK_SECURITY, CONFIRM_ADD = range(6)


@admin_only
async def inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show inbounds management menu."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.INB_LIST_ALL, callback_data=CB_INBOUND_LIST)],
        [InlineKeyboardButton(lang.INB_ADD, callback_data=CB_INBOUND_ADD)],
        [back_button(CB_MAIN_MENU)],
    ])
    await answer_and_edit(update.callback_query, lang.INB_MANAGEMENT, reply_markup=keyboard)


@admin_only
async def inbounds_menu_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show inbounds menu from reply keyboard text."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.INB_LIST_ALL, callback_data=CB_INBOUND_LIST)],
        [InlineKeyboardButton(lang.INB_ADD, callback_data=CB_INBOUND_ADD)],
        [back_button(CB_MAIN_MENU)],
    ])
    await update.message.reply_text(lang.INB_MANAGEMENT, reply_markup=keyboard, parse_mode="HTML")


@admin_only
async def list_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all inbounds with pagination."""
    api = get_api(context)
    query = update.callback_query
    await query.answer()

    try:
        result = await api.get_inbounds()
        if not result.get("success"):
            await query.edit_message_text(
                lang.FAILED.format(msg=result.get("msg", "")),
                reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUNDS)]]),
                parse_mode="HTML",
            )
            return

        inbounds = result.get("obj", [])
        if not inbounds:
            await query.edit_message_text(
                lang.INB_LIST_EMPTY,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(lang.INB_ADD, callback_data=CB_INBOUND_ADD)],
                    [back_button(CB_INBOUNDS)],
                ]),
                parse_mode="HTML",
            )
            return

        page = 0
        if query.data and ":" in query.data:
            try:
                page = int(query.data.split(":")[1])
            except (ValueError, IndexError):
                page = 0

        items = []
        for inb in inbounds:
            status = "✅" if inb.get("enable") else "❌"
            protocol = inb.get("protocol", "?").upper()
            remark = inb.get("remark", "unnamed")
            port = inb.get("port", "?")
            label = f"{status} {remark} | {protocol}:{port}"
            items.append((label, f"{CB_INBOUND_VIEW}:{inb['id']}"))

        keyboard = paginate_buttons(
            items, page=page, per_page=8, n_cols=1,
            back_cb=CB_INBOUNDS, page_prefix="inb_page",
        )

        await query.edit_message_text(
            lang.INB_LIST_TITLE.format(count=len(inbounds)),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Error listing inbounds: %s", e)
        await query.edit_message_text(
            lang.ERROR.format(error=e),
            reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUNDS)]]),
            parse_mode="HTML",
        )


@admin_only
async def view_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed info for a single inbound."""
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
            await query.edit_message_text(
                lang.FAILED.format(msg=result.get("msg", "")),
                reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUND_LIST)]]),
                parse_mode="HTML",
            )
            return

        inbound = result["obj"]
        text = format_inbound_detail(inbound)

        enable_text = "❌ غیرفعال کردن" if inbound.get("enable") else "✅ فعال کردن"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(enable_text, callback_data=f"{CB_INBOUND_TOGGLE}:{inbound_id}"),
                InlineKeyboardButton("🗑 حذف", callback_data=f"{CB_INBOUND_DEL}:{inbound_id}"),
            ],
            [InlineKeyboardButton(lang.INB_VIEW_CLIENTS, callback_data=f"{CB_INBOUND_CLIENTS}:{inbound_id}")],
            [InlineKeyboardButton(lang.BTN_REFRESH, callback_data=f"{CB_INBOUND_VIEW}:{inbound_id}")],
            [back_button(CB_INBOUND_LIST)],
        ])

        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error("Error viewing inbound: %s", e)
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


@admin_only
async def toggle_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle inbound enable/disable."""
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
            await query.edit_message_text(lang.FAILED.format(msg=result.get("msg", "")), parse_mode="HTML")
            return

        inbound = result["obj"]
        inbound["enable"] = not inbound.get("enable", True)
        update_result = await api.update_inbound(inbound_id, inbound)

        if update_result.get("success"):
            remark = inbound.get("remark", "")
            if inbound["enable"]:
                text = lang.INB_TOGGLE_ENABLED.format(remark=remark)
            else:
                text = lang.INB_TOGGLE_DISABLED.format(remark=remark)
        else:
            text = lang.FAILED.format(msg=update_result.get("msg", ""))

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 مشاهده", callback_data=f"{CB_INBOUND_VIEW}:{inbound_id}")],
                [back_button(CB_INBOUND_LIST)],
            ]),
            parse_mode="HTML",
        )
    except Exception as e:
        await query.edit_message_text(lang.ERROR.format(error=e), parse_mode="HTML")


@admin_only
async def delete_inbound_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lang.BTN_CONFIRM_YES + "، حذف شود", callback_data=f"inb_del_yes:{inbound_id}"),
            InlineKeyboardButton(lang.BTN_CANCEL, callback_data=f"{CB_INBOUND_VIEW}:{inbound_id}"),
        ],
    ])
    await query.edit_message_text(
        lang.INB_DELETE_CONFIRM.format(id=inbound_id),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@admin_only
async def delete_inbound_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return

    api = get_api(context)
    try:
        result = await api.delete_inbound(inbound_id)
        text = lang.INB_DELETE_SUCCESS if result.get("success") else lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUND_LIST)]]),
        parse_mode="HTML",
    )


@admin_only
async def inbound_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        inbound_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return
    query.data = f"cl_list_inb:{inbound_id}"
    from handlers.clients import list_clients_for_inbound
    await list_clients_for_inbound(update, context)


# ─── Add Inbound Conversation ─────────────────────────────────────────────────

@admin_only
async def add_inbound_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("VMESS", callback_data="proto:vmess"),
            InlineKeyboardButton("VLESS", callback_data="proto:vless"),
        ],
        [
            InlineKeyboardButton("Trojan", callback_data="proto:trojan"),
            InlineKeyboardButton("Shadowsocks", callback_data="proto:shadowsocks"),
        ],
        [InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_inb_cancel")],
    ])
    await query.edit_message_text(
        f"{lang.INB_ADD_TITLE}\n\n{lang.INB_ADD_PROTOCOL}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ASK_PROTOCOL


@admin_only
async def add_inbound_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    protocol = query.data.split(":")[1]
    context.user_data["new_inbound"] = {"protocol": protocol}

    await query.edit_message_text(
        f"{lang.INB_ADD_TITLE}\n\nپروتکل: <b>{protocol.upper()}</b>\n\n{lang.INB_ADD_REMARK}",
        parse_mode="HTML",
    )
    return ASK_REMARK


@admin_only
async def add_inbound_remark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    remark = update.message.text.strip()
    if not remark or len(remark) > 50:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_REMARK

    context.user_data["new_inbound"]["remark"] = remark
    data = context.user_data["new_inbound"]
    await update.message.reply_text(
        f"{lang.INB_ADD_TITLE}\n\nپروتکل: <b>{data['protocol'].upper()}</b>\n"
        f"نام: <b>{remark}</b>\n\n{lang.INB_ADD_PORT}",
        parse_mode="HTML",
    )
    return ASK_PORT


@admin_only
async def add_inbound_port(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        port = int(update.message.text.strip())
        if port < 1 or port > 65535:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(lang.INVALID_INPUT, parse_mode="HTML")
        return ASK_PORT

    context.user_data["new_inbound"]["port"] = port
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("TCP", callback_data="net:tcp"),
            InlineKeyboardButton("WebSocket", callback_data="net:ws"),
        ],
        [
            InlineKeyboardButton("gRPC", callback_data="net:grpc"),
            InlineKeyboardButton("HTTPUpgrade", callback_data="net:httpupgrade"),
        ],
        [InlineKeyboardButton("SplitHTTP", callback_data="net:splithttp")],
        [InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_inb_cancel")],
    ])
    data = context.user_data["new_inbound"]
    await update.message.reply_text(
        f"{lang.INB_ADD_TITLE}\n\nپروتکل: <b>{data['protocol'].upper()}</b> | "
        f"نام: <b>{data['remark']}</b> | پورت: <b>{port}</b>\n\n{lang.INB_ADD_NETWORK}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ASK_NETWORK


@admin_only
async def add_inbound_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    network = query.data.split(":")[1]
    context.user_data["new_inbound"]["network"] = network

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("None", callback_data="sec:none"),
            InlineKeyboardButton("TLS", callback_data="sec:tls"),
        ],
        [InlineKeyboardButton("Reality", callback_data="sec:reality")],
        [InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_inb_cancel")],
    ])
    data = context.user_data["new_inbound"]
    await query.edit_message_text(
        f"{lang.INB_ADD_TITLE}\n\nپروتکل: <b>{data['protocol'].upper()}</b> | "
        f"شبکه: <b>{network}</b>\n\n{lang.INB_ADD_SECURITY}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return ASK_SECURITY


@admin_only
async def add_inbound_security(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    security = query.data.split(":")[1]
    context.user_data["new_inbound"]["security"] = security
    data = context.user_data["new_inbound"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ایجاد", callback_data="add_inb_confirm"),
            InlineKeyboardButton(lang.BTN_CANCEL, callback_data="add_inb_cancel"),
        ],
    ])
    await query.edit_message_text(
        f"{lang.INB_ADD_CONFIRM}\n\n"
        f"<b>پروتکل:</b> {data['protocol'].upper()}\n"
        f"<b>نام:</b> {data['remark']}\n"
        f"<b>پورت:</b> {data['port']}\n"
        f"<b>شبکه:</b> {data['network']}\n"
        f"<b>امنیت:</b> {security}\n\n"
        f"ایجاد شود؟",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return CONFIRM_ADD


@admin_only
async def add_inbound_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("new_inbound", {})
    protocol = data.get("protocol", "vless")
    remark = data.get("remark", "new")
    port = data.get("port", 443)
    network = data.get("network", "tcp")
    security = data.get("security", "none")

    client_uuid = generate_uuid()
    sub_id = generate_sub_id()
    default_client = {
        "id": client_uuid, "email": remark, "enable": True,
        "totalGB": 0, "expiryTime": 0, "limitIp": 0,
        "flow": "", "tgId": "", "subId": sub_id, "reset": 0,
    }

    if protocol == "trojan":
        default_client["password"] = generate_password()
        settings = {"clients": [default_client], "fallbacks": []}
    elif protocol == "shadowsocks":
        settings = {"method": "chacha20-ietf-poly1305", "password": generate_password(), "network": "tcp,udp", "clients": []}
    else:
        if protocol == "vless":
            settings = {"clients": [default_client], "decryption": "none", "fallbacks": []}
        else:
            settings = {"clients": [default_client]}

    stream = {"network": network, "security": security}
    if network == "ws":
        stream["wsSettings"] = {"path": "/", "headers": {}}
    elif network == "grpc":
        stream["grpcSettings"] = {"serviceName": "", "multiMode": False}
    elif network == "httpupgrade":
        stream["httpupgradeSettings"] = {"path": "/", "host": ""}
    elif network == "splithttp":
        stream["splithttpSettings"] = {"path": "/", "host": ""}
    elif network == "tcp":
        stream["tcpSettings"] = {"header": {"type": "none"}}

    if security == "tls":
        stream["tlsSettings"] = {"serverName": "", "certificates": [{"certificateFile": "", "keyFile": ""}], "alpn": ["h2", "http/1.1"], "fingerprint": "chrome"}
    elif security == "reality":
        stream["realitySettings"] = {"show": False, "dest": "google.com:443", "xver": 0, "serverNames": ["google.com"], "privateKey": "", "publicKey": "", "shortIds": [generate_sub_id(8)], "fingerprint": "chrome"}

    inbound_data = {
        "up": 0, "down": 0, "total": 0, "remark": remark,
        "enable": True, "expiryTime": 0, "port": port, "protocol": protocol,
        "settings": json.dumps(settings),
        "streamSettings": json.dumps(stream),
        "sniffing": json.dumps({"enabled": True, "destOverride": ["http", "tls", "quic", "fakedns"]}),
        "allocate": json.dumps({"strategy": "always", "refresh": 5, "concurrency": 3}),
    }

    api = get_api(context)
    try:
        result = await api.add_inbound(inbound_data)
        if result.get("success"):
            new_id = result.get("obj", {}).get("id", "?")
            text = (
                f"{lang.INB_ADD_SUCCESS}\n\n"
                f"<b>شناسه:</b> {new_id}\n"
                f"<b>پروتکل:</b> {protocol.upper()}\n"
                f"<b>نام:</b> {remark}\n"
                f"<b>پورت:</b> {port}"
            )
        else:
            text = lang.FAILED.format(msg=result.get("msg", ""))
    except Exception as e:
        text = lang.ERROR.format(error=e)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUND_LIST)]]),
        parse_mode="HTML",
    )
    context.user_data.pop("new_inbound", None)
    return ConversationHandler.END


async def add_inbound_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("new_inbound", None)
    await query.edit_message_text(
        lang.INB_ADD_CANCEL,
        reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUNDS)]]),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def add_inbound_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_inbound", None)
    await update.message.reply_text(lang.INB_ADD_CANCEL, reply_markup=InlineKeyboardMarkup([[back_button(CB_INBOUNDS)]]), parse_mode="HTML")
    return ConversationHandler.END


@admin_only
async def inbound_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await list_inbounds(update, context)


def register(app) -> None:
    """Register all inbound handlers."""
    app.add_handler(CallbackQueryHandler(inbounds_menu, pattern=f"^{CB_INBOUNDS}$"))
    app.add_handler(CallbackQueryHandler(list_inbounds, pattern=f"^{CB_INBOUND_LIST}$"))
    app.add_handler(CallbackQueryHandler(inbound_page, pattern=r"^inb_page:\d+$"))
    app.add_handler(CallbackQueryHandler(view_inbound, pattern=rf"^{CB_INBOUND_VIEW}:\d+$"))
    app.add_handler(CallbackQueryHandler(toggle_inbound, pattern=rf"^{CB_INBOUND_TOGGLE}:\d+$"))
    app.add_handler(CallbackQueryHandler(delete_inbound_confirm, pattern=rf"^{CB_INBOUND_DEL}:\d+$"))
    app.add_handler(CallbackQueryHandler(delete_inbound_execute, pattern=r"^inb_del_yes:\d+$"))
    app.add_handler(CallbackQueryHandler(inbound_clients, pattern=rf"^{CB_INBOUND_CLIENTS}:\d+$"))

    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_inbound_start, pattern=f"^{CB_INBOUND_ADD}$")],
        states={
            ASK_PROTOCOL: [CallbackQueryHandler(add_inbound_protocol, pattern=r"^proto:")],
            ASK_REMARK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_inbound_remark)],
            ASK_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_inbound_port)],
            ASK_NETWORK: [CallbackQueryHandler(add_inbound_network, pattern=r"^net:")],
            ASK_SECURITY: [CallbackQueryHandler(add_inbound_security, pattern=r"^sec:")],
            CONFIRM_ADD: [CallbackQueryHandler(add_inbound_execute, pattern=r"^add_inb_confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(add_inbound_cancel, pattern=r"^add_inb_cancel$"),
            MessageHandler(filters.Regex(r"^/cancel$"), add_inbound_cancel_cmd),
        ],
        per_message=False,
    )
    app.add_handler(add_conv)
