"""Data models for 3x-ui API responses and requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClientStat:
    """Traffic statistics for a single client."""
    id: int = 0
    inbound_id: int = 0
    enable: bool = True
    email: str = ""
    up: int = 0
    down: int = 0
    total: int = 0
    expiry_time: int = 0
    reset: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientStat":
        return cls(
            id=data.get("id", 0),
            inbound_id=data.get("inboundId", 0),
            enable=data.get("enable", True),
            email=data.get("email", ""),
            up=data.get("up", 0),
            down=data.get("down", 0),
            total=data.get("total", 0),
            expiry_time=data.get("expiryTime", 0),
            reset=data.get("reset", 0),
        )


@dataclass
class Client:
    """A client entry within an inbound."""
    id: str = ""          # UUID for VMESS/VLESS, password for Trojan
    email: str = ""
    enable: bool = True
    total_gb: int = 0     # traffic limit in bytes, 0 = unlimited
    expiry_time: int = 0  # expiry timestamp ms, 0 = never
    limit_ip: int = 0     # IP limit, 0 = unlimited
    flow: str = ""        # for VLESS (xtls-rprx-vision)
    tg_id: str = ""
    sub_id: str = ""
    reset: int = 0
    # Trojan specific
    password: str = ""
    # Shadowsocks specific
    method: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Client":
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            enable=data.get("enable", True),
            total_gb=data.get("totalGB", 0),
            expiry_time=data.get("expiryTime", 0),
            limit_ip=data.get("limitIp", 0),
            flow=data.get("flow", ""),
            tg_id=data.get("tgId", ""),
            sub_id=data.get("subId", ""),
            reset=data.get("reset", 0),
            password=data.get("password", ""),
            method=data.get("method", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "email": self.email,
            "enable": self.enable,
            "totalGB": self.total_gb,
            "expiryTime": self.expiry_time,
            "limitIp": self.limit_ip,
            "flow": self.flow,
            "tgId": self.tg_id,
            "subId": self.sub_id,
            "reset": self.reset,
        }
        if self.password:
            d["password"] = self.password
        if self.method:
            d["method"] = self.method
        return d


@dataclass
class StreamSettings:
    """Stream/network settings for an inbound."""
    network: str = "tcp"
    security: str = "none"
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StreamSettings":
        if isinstance(data, str):
            import json
            data = json.loads(data) if data else {}
        return cls(
            network=data.get("network", "tcp"),
            security=data.get("security", "none"),
            raw=data,
        )


@dataclass
class Inbound:
    """A single inbound configuration."""
    id: int = 0
    up: int = 0
    down: int = 0
    total: int = 0
    remark: str = ""
    enable: bool = True
    expiry_time: int = 0
    port: int = 0
    protocol: str = ""
    settings: str = ""
    stream_settings: str = ""
    tag: str = ""
    sniffing: str = ""
    allocate: str = ""
    client_stats: list[ClientStat] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Inbound":
        stats = [ClientStat.from_dict(s) for s in data.get("clientStats", []) or []]
        return cls(
            id=data.get("id", 0),
            up=data.get("up", 0),
            down=data.get("down", 0),
            total=data.get("total", 0),
            remark=data.get("remark", ""),
            enable=data.get("enable", True),
            expiry_time=data.get("expiryTime", 0),
            port=data.get("port", 0),
            protocol=data.get("protocol", ""),
            settings=data.get("settings", ""),
            stream_settings=data.get("streamSettings", ""),
            tag=data.get("tag", ""),
            sniffing=data.get("sniffing", ""),
            allocate=data.get("allocate", ""),
            client_stats=stats,
        )

    def get_clients(self) -> list[Client]:
        """Parse clients from the settings JSON."""
        import json
        try:
            settings = json.loads(self.settings) if isinstance(self.settings, str) else self.settings
            raw_clients = settings.get("clients", [])
            return [Client.from_dict(c) for c in raw_clients]
        except (json.JSONDecodeError, AttributeError):
            return []

    def get_stream_settings(self) -> StreamSettings:
        """Parse stream settings JSON."""
        import json
        try:
            data = json.loads(self.stream_settings) if isinstance(self.stream_settings, str) else self.stream_settings
            return StreamSettings.from_dict(data)
        except (json.JSONDecodeError, AttributeError):
            return StreamSettings()


@dataclass
class ServerStatus:
    """Server resource status."""
    cpu: float = 0.0
    mem_current: int = 0
    mem_total: int = 0
    disk_current: int = 0
    disk_total: int = 0
    xray_version: str = ""
    xray_running: bool = False
    uptime: int = 0
    loads: list[float] = field(default_factory=list)
    net_io: dict[str, int] = field(default_factory=dict)
    tcp_count: int = 0
    udp_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServerStatus":
        obj = data.get("obj", data)
        cpu_info = obj.get("cpu", 0)
        mem = obj.get("mem", {})
        disk = obj.get("disk", {})
        xray = obj.get("xray", {})
        net = obj.get("netIO", {})

        return cls(
            cpu=cpu_info if isinstance(cpu_info, (int, float)) else 0,
            mem_current=mem.get("current", 0),
            mem_total=mem.get("total", 0),
            disk_current=disk.get("current", 0),
            disk_total=disk.get("total", 0),
            xray_version=xray.get("version", "unknown"),
            xray_running=xray.get("state", "") == "running",
            uptime=obj.get("uptime", 0),
            loads=obj.get("loads", []),
            net_io=net,
            tcp_count=obj.get("tcpCount", 0),
            udp_count=obj.get("udpCount", 0),
        )
