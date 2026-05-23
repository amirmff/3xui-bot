"""Helper utilities: UUID generation, link building, QR codes."""

from __future__ import annotations

import base64
import io
import json
import uuid
import random
import string
from typing import Any
from urllib.parse import quote


def generate_uuid() -> str:
    """Generate a random UUID v4."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a random hex short ID (for Reality)."""
    return "".join(random.choices("0123456789abcdef", k=length))


def generate_password(length: int = 16) -> str:
    """Generate a random password for Trojan."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def generate_sub_id(length: int = 16) -> str:
    """Generate a random subscription ID."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def bytes_to_gb(b: int) -> float:
    """Convert bytes to GB."""
    return b / (1024 ** 3)


def gb_to_bytes(gb: float) -> int:
    """Convert GB to bytes."""
    return int(gb * (1024 ** 3))


def days_to_timestamp_ms(days: int) -> int:
    """Convert days-from-now to a future Unix timestamp in milliseconds."""
    import time
    if days <= 0:
        return 0
    return int((time.time() + days * 86400) * 1000)


def build_vmess_link(
    address: str,
    port: int,
    uuid_str: str,
    remark: str = "",
    network: str = "tcp",
    tls: str = "none",
    sni: str = "",
    path: str = "",
    host: str = "",
    aid: int = 0,
) -> str:
    """Build a VMess connection link."""
    vmess_config = {
        "v": "2",
        "ps": remark,
        "add": address,
        "port": str(port),
        "id": uuid_str,
        "aid": str(aid),
        "scy": "auto",
        "net": network,
        "type": "none",
        "host": host,
        "path": path,
        "tls": tls if tls != "none" else "",
        "sni": sni,
    }
    json_str = json.dumps(vmess_config)
    b64 = base64.urlsafe_b64encode(json_str.encode()).decode()
    return f"vmess://{b64}"


def build_vless_link(
    address: str,
    port: int,
    uuid_str: str,
    remark: str = "",
    network: str = "tcp",
    security: str = "none",
    sni: str = "",
    path: str = "",
    host: str = "",
    flow: str = "",
    fp: str = "chrome",
    pbk: str = "",
    sid: str = "",
    spider_x: str = "",
    alpn: str = "",
    encryption: str = "none",
    header_type: str = "none",
    service_name: str = "",
) -> str:
    """Build a VLESS connection link."""
    params: list[str] = [
        f"type={network}",
        f"security={security}",
        f"encryption={encryption}",
    ]

    if flow:
        params.append(f"flow={flow}")
    if sni:
        params.append(f"sni={sni}")
    if fp:
        params.append(f"fp={fp}")
    if alpn:
        params.append(f"alpn={quote(alpn)}")
    if header_type and header_type != "none":
        params.append(f"headerType={header_type}")

    # Network-specific
    if network == "ws":
        if path:
            params.append(f"path={quote(path)}")
        if host:
            params.append(f"host={host}")
    elif network == "grpc":
        if service_name:
            params.append(f"serviceName={service_name}")
    elif network in ("httpupgrade", "splithttp"):
        if path:
            params.append(f"path={quote(path)}")
        if host:
            params.append(f"host={host}")

    # Security-specific
    if security == "reality":
        if pbk:
            params.append(f"pbk={pbk}")
        if sid:
            params.append(f"sid={sid}")
        if spider_x:
            params.append(f"spx={quote(spider_x)}")

    param_str = "&".join(params)
    encoded_remark = quote(remark)
    return f"vless://{uuid_str}@{address}:{port}?{param_str}#{encoded_remark}"


def build_trojan_link(
    address: str,
    port: int,
    password: str,
    remark: str = "",
    network: str = "tcp",
    security: str = "tls",
    sni: str = "",
    path: str = "",
    host: str = "",
    fp: str = "chrome",
    alpn: str = "",
    header_type: str = "none",
    service_name: str = "",
    pbk: str = "",
    sid: str = "",
) -> str:
    """Build a Trojan connection link."""
    params: list[str] = [
        f"type={network}",
        f"security={security}",
    ]

    if sni:
        params.append(f"sni={sni}")
    if fp:
        params.append(f"fp={fp}")
    if alpn:
        params.append(f"alpn={quote(alpn)}")
    if header_type and header_type != "none":
        params.append(f"headerType={header_type}")

    if network == "ws":
        if path:
            params.append(f"path={quote(path)}")
        if host:
            params.append(f"host={host}")
    elif network == "grpc":
        if service_name:
            params.append(f"serviceName={service_name}")

    if security == "reality":
        if pbk:
            params.append(f"pbk={pbk}")
        if sid:
            params.append(f"sid={sid}")

    param_str = "&".join(params)
    encoded_remark = quote(remark)
    return f"trojan://{password}@{address}:{port}?{param_str}#{encoded_remark}"


def build_shadowsocks_link(
    address: str,
    port: int,
    password: str,
    method: str = "aes-256-gcm",
    remark: str = "",
) -> str:
    """Build a Shadowsocks connection link."""
    user_info = f"{method}:{password}"
    b64 = base64.urlsafe_b64encode(user_info.encode()).decode().rstrip("=")
    encoded_remark = quote(remark)
    return f"ss://{b64}@{address}:{port}#{encoded_remark}"


def build_connection_link(
    protocol: str,
    address: str,
    inbound: dict[str, Any],
    client: dict[str, Any],
) -> str:
    """Build the appropriate connection link based on protocol."""
    port = inbound.get("port", 443)
    remark = f"{inbound.get('remark', '')}-{client.get('email', '')}"

    # Parse stream settings
    try:
        stream = json.loads(inbound.get("streamSettings", "{}"))
    except (json.JSONDecodeError, TypeError):
        stream = {}

    network = stream.get("network", "tcp")
    security = stream.get("security", "none")

    # Common params from stream settings
    sni = ""
    path = ""
    host = ""
    fp = "chrome"
    pbk = ""
    sid = ""
    alpn = ""
    service_name = ""

    # Extract TLS settings
    tls_settings = stream.get("tlsSettings", stream.get("realitySettings", {})) or {}
    sni = tls_settings.get("serverName", "")
    fp = tls_settings.get("fingerprint", "chrome")
    alpn_list = tls_settings.get("alpn", [])
    if alpn_list:
        alpn = ",".join(alpn_list)

    # Reality settings
    reality = stream.get("realitySettings", {}) or {}
    if reality:
        pbk = reality.get("publicKey", "")
        sid = reality.get("shortId", "")
        sni = reality.get("serverNames", [sni])[0] if reality.get("serverNames") else sni
        fp = reality.get("fingerprint", fp)

    # Network-specific settings
    net_key = f"{network}Settings"
    net_settings = stream.get(net_key, {}) or {}
    if network == "ws":
        path = net_settings.get("path", "/")
        headers = net_settings.get("headers", {})
        host = headers.get("Host", headers.get("host", ""))
    elif network == "grpc":
        service_name = net_settings.get("serviceName", "")
    elif network in ("httpupgrade", "splithttp"):
        path = net_settings.get("path", "/")
        host = net_settings.get("host", "")

    if protocol == "vmess":
        return build_vmess_link(
            address=address, port=port, uuid_str=client.get("id", ""),
            remark=remark, network=network,
            tls=security, sni=sni, path=path, host=host,
        )
    elif protocol == "vless":
        return build_vless_link(
            address=address, port=port, uuid_str=client.get("id", ""),
            remark=remark, network=network, security=security,
            sni=sni, path=path, host=host, flow=client.get("flow", ""),
            fp=fp, pbk=pbk, sid=sid, alpn=alpn, service_name=service_name,
        )
    elif protocol == "trojan":
        return build_trojan_link(
            address=address, port=port, password=client.get("password", client.get("id", "")),
            remark=remark, network=network, security=security,
            sni=sni, path=path, host=host, fp=fp, alpn=alpn,
            service_name=service_name, pbk=pbk, sid=sid,
        )
    elif protocol == "shadowsocks":
        # For SS, the password & method are in inbound settings
        try:
            settings = json.loads(inbound.get("settings", "{}"))
            method = settings.get("method", "aes-256-gcm")
            ss_password = settings.get("password", "")
            # Combine inbound password + client password
            full_pass = f"{ss_password}:{client.get('password', client.get('email', ''))}"
        except (json.JSONDecodeError, TypeError):
            method = "aes-256-gcm"
            full_pass = client.get("password", "")
        return build_shadowsocks_link(
            address=address, port=port, password=full_pass,
            method=method, remark=remark,
        )
    else:
        return f"# Unsupported protocol: {protocol}"


def generate_qr_code(data: str) -> bytes:
    """Generate a QR code image from data and return as PNG bytes."""
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
