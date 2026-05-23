"""Message formatting utilities — Persian output."""

from __future__ import annotations

import lang as L


def format_bytes(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


def format_traffic(up: int, down: int, total_limit: int = 0) -> str:
    used = up + down
    parts = [
        f"↑ {format_bytes(up)}",
        f"↓ {format_bytes(down)}",
        f"📊 مصرف: {format_bytes(used)}",
    ]
    if total_limit > 0:
        parts.append(f"📦 حد مجاز: {format_bytes(total_limit)}")
        pct = min((used / total_limit) * 100, 100) if total_limit else 0
        parts.append(f"📈 {progress_bar(pct)} {pct:.1f}%")
    else:
        parts.append(f"📦 حد مجاز: {L.FMT_UNLIMITED}")
    return "\n".join(parts)


def format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts: list[str] = []
    if days > 0:
        parts.append(f"{days} روز")
    if hours > 0:
        parts.append(f"{hours} ساعت")
    parts.append(f"{minutes} دقیقه")
    return " ".join(parts)


def format_expiry(timestamp_ms: int) -> str:
    if timestamp_ms == 0:
        return L.FMT_NEVER
    import time
    from datetime import datetime, timezone

    expiry = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    delta = expiry - now
    date_str = expiry.strftime("%Y-%m-%d %H:%M")

    if delta.total_seconds() <= 0:
        return L.FMT_EXPIRED.format(date=date_str)
    elif delta.days > 0:
        return L.FMT_EXPIRY.format(date=date_str, remaining=L.FMT_DAYS_LEFT.format(days=delta.days))
    else:
        hours = int(delta.total_seconds() // 3600)
        return L.FMT_EXPIRY_HOURS.format(date=date_str, hours=hours)


def progress_bar(percentage: float, length: int = 10) -> str:
    filled = int(length * percentage / 100)
    empty = length - filled
    return "█" * filled + "░" * empty


def format_server_status(status: dict) -> str:
    obj = status.get("obj", status)
    cpu = obj.get("cpu", 0)
    mem = obj.get("mem", {})
    disk = obj.get("disk", {})
    xray = obj.get("xray", {})
    uptime = obj.get("uptime", 0)
    net = obj.get("netIO", {})

    mem_current = mem.get("current", 0)
    mem_total = mem.get("total", 0)
    mem_pct = (mem_current / mem_total * 100) if mem_total else 0

    disk_current = disk.get("current", 0)
    disk_total = disk.get("total", 0)
    disk_pct = (disk_current / disk_total * 100) if disk_total else 0

    xray_state = L.FMT_RUNNING if xray.get("state") == "running" else L.FMT_STOPPED
    xray_ver = xray.get("version", "unknown")
    tcp_count = obj.get("tcpCount", 0)
    udp_count = obj.get("udpCount", 0)
    net_up = net.get("up", 0)
    net_down = net.get("down", 0)

    lines = [
        "🖥 <b>وضعیت سرور</b>",
        "",
        f"<b>CPU:</b> {cpu:.1f}% {progress_bar(cpu)}",
        f"<b>RAM:</b> {format_bytes(mem_current)}/{format_bytes(mem_total)} ({mem_pct:.1f}%) {progress_bar(mem_pct)}",
        f"<b>Disk:</b> {format_bytes(disk_current)}/{format_bytes(disk_total)} ({disk_pct:.1f}%) {progress_bar(disk_pct)}",
        f"<b>آپتایم:</b> {format_uptime(uptime)}",
        "",
        f"<b>Xray:</b> {xray_state}",
        f"<b>نسخه Xray:</b> <code>{xray_ver}</code>",
        "",
        f"<b>اتصالات:</b> TCP: {tcp_count} | UDP: {udp_count}",
        f"<b>شبکه:</b> ↑ {format_bytes(net_up)}/s | ↓ {format_bytes(net_down)}/s",
    ]
    return "\n".join(lines)


def format_inbound_short(inbound: dict) -> str:
    status = "✅" if inbound.get("enable") else "❌"
    protocol = inbound.get("protocol", "?").upper()
    port = inbound.get("port", "?")
    remark = inbound.get("remark", "unnamed")
    up = inbound.get("up", 0)
    down = inbound.get("down", 0)
    total = format_bytes(up + down)
    return f"{status} <b>{remark}</b> | {protocol} | پورت: {port} | ترافیک: {total}"


def format_inbound_detail(inbound: dict) -> str:
    import json

    status = L.FMT_ENABLED if inbound.get("enable") else L.FMT_DISABLED
    protocol = inbound.get("protocol", "?").upper()
    port = inbound.get("port", "?")
    remark = inbound.get("remark", "unnamed")
    up = inbound.get("up", 0)
    down = inbound.get("down", 0)
    total_limit = inbound.get("total", 0)
    expiry = format_expiry(inbound.get("expiryTime", 0))

    try:
        stream = json.loads(inbound.get("streamSettings", "{}"))
        network = stream.get("network", "?")
        security = stream.get("security", "none")
    except (json.JSONDecodeError, TypeError):
        network = "?"
        security = "?"

    try:
        settings = json.loads(inbound.get("settings", "{}"))
        client_count = len(settings.get("clients", []))
    except (json.JSONDecodeError, TypeError):
        client_count = 0

    lines = [
        f"📋 <b>اینباند: {remark}</b>",
        "",
        f"<b>وضعیت:</b> {status}",
        f"<b>پروتکل:</b> {protocol}",
        f"<b>پورت:</b> {port}",
        f"<b>شبکه:</b> {network}",
        f"<b>امنیت:</b> {security}",
        f"<b>انقضا:</b> {expiry}",
        f"<b>کاربران:</b> {client_count}",
        "",
        f"<b>ترافیک:</b>",
        format_traffic(up, down, total_limit),
    ]
    return "\n".join(lines)


def format_client_detail(client: dict, stat: dict | None = None) -> str:
    email = client.get("email", "unknown")
    enable = L.FMT_ENABLED if client.get("enable", True) else L.FMT_DISABLED
    total_gb = client.get("totalGB", 0)
    expiry = format_expiry(client.get("expiryTime", 0))
    limit_ip = client.get("limitIp", 0)
    ip_str = str(limit_ip) if limit_ip > 0 else L.FMT_UNLIMITED

    lines = [
        f"👤 <b>کاربر: {email}</b>",
        "",
        f"<b>وضعیت:</b> {enable}",
        f"<b>انقضا:</b> {expiry}",
        f"<b>محدودیت IP:</b> {ip_str}",
    ]

    if stat:
        up = stat.get("up", 0)
        down = stat.get("down", 0)
        total_limit = total_gb
        lines.append("")
        lines.append("<b>ترافیک:</b>")
        lines.append(format_traffic(up, down, total_limit))
    elif total_gb > 0:
        lines.append(f"<b>حد ترافیک:</b> {format_bytes(total_gb)}")
    else:
        lines.append(f"<b>حد ترافیک:</b> {L.FMT_UNLIMITED}")

    return "\n".join(lines)


def format_online_clients(emails: list[str]) -> str:
    if not emails:
        return L.ONLINE_EMPTY
    lines = [L.ONLINE_TITLE.format(count=len(emails)), ""]
    for i, email in enumerate(emails, 1):
        lines.append(f"  {i}. <code>{email}</code>")
    return "\n".join(lines)
