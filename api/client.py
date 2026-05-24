"""Async HTTP client for the 3x-ui panel API with proxy support."""

from __future__ import annotations

import json
import logging
import ssl as _ssl
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class XUIClient:
    """Async client for 3x-ui REST API with automatic session management and proxy support."""

    def __init__(self, base_url: str = "", username: str = "admin",
                 password: str = "admin", verify_ssl: bool = False,
                 proxy_url: str = ""):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.proxy_url = proxy_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._logged_in: bool = False

    def _get_ssl_context(self):
        """Get SSL context — skip verification if verify_ssl is False."""
        if not self.verify_ssl:
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            return ctx
        return None  # Use default SSL

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session with optional proxy support."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            if self.proxy_url:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(
                    self.proxy_url, rdns=False
                )
                logger.info("Using proxy: %s", self.proxy_url.split("@")[-1] if "@" in self.proxy_url else self.proxy_url)
            else:
                connector = aiohttp.TCPConnector()

            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            self._logged_in = False
        return self._session

    async def login(self) -> bool:
        """Authenticate with the panel and store session cookie."""
        session = await self._get_session()
        url = f"{self.base_url}/login"
        payload = {"username": self.username, "password": self.password}
        ssl_ctx = self._get_ssl_context()
        try:
            async with session.post(url, data=payload, ssl=ssl_ctx) as resp:
                data = await resp.json()
                if data.get("success"):
                    self._logged_in = True
                    logger.info("Successfully logged in to 3x-ui panel")
                    return True
                else:
                    logger.error("Login failed: %s", data.get("msg", "Unknown error"))
                    return False
        except Exception as e:
            logger.error("Login error: %s", e)
            return False

    async def _ensure_login(self) -> None:
        """Ensure we have an active session."""
        if not self._logged_in:
            success = await self.login()
            if not success:
                raise ConnectionError("Failed to login to 3x-ui panel")

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an authenticated API request with auto re-login on 401."""
        await self._ensure_login()
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        kwargs.setdefault("ssl", self._get_ssl_context())

        async with session.request(method, url, **kwargs) as resp:
            if resp.status == 401 or resp.status == 403:
                # Session expired, re-login and retry
                logger.info("Session expired, re-logging in...")
                self._logged_in = False
                await self._ensure_login()
                async with session.request(method, url, **kwargs) as retry_resp:
                    return await self._parse_response(retry_resp)
            return await self._parse_response(resp)

    async def _parse_response(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        """Parse the API response."""
        try:
            data = await resp.json()
        except Exception:
            text = await resp.text()
            data = {"success": False, "msg": f"Non-JSON response: {text[:200]}"}
        return data

    async def _get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", path, **kwargs)

    # ─── Inbounds API ─────────────────────────────────────────────────────

    async def get_inbounds(self) -> dict[str, Any]:
        """Get all inbounds."""
        return await self._get("/panel/api/inbounds/list")

    async def get_inbound(self, inbound_id: int) -> dict[str, Any]:
        """Get a single inbound by ID."""
        return await self._get(f"/panel/api/inbounds/get/{inbound_id}")

    async def add_inbound(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add a new inbound."""
        return await self._post("/panel/api/inbounds/add", json=data)

    async def update_inbound(self, inbound_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing inbound."""
        return await self._post(f"/panel/api/inbounds/update/{inbound_id}", json=data)

    async def delete_inbound(self, inbound_id: int) -> dict[str, Any]:
        """Delete an inbound."""
        return await self._post(f"/panel/api/inbounds/del/{inbound_id}")

    # ─── Client Traffic API ───────────────────────────────────────────────

    async def get_client_traffics(self, email: str) -> dict[str, Any]:
        """Get client traffic stats by email."""
        return await self._get(f"/panel/api/inbounds/getClientTraffics/{email}")

    async def get_client_traffics_by_id(self, inbound_id: int) -> dict[str, Any]:
        """Get client traffic stats by inbound ID."""
        return await self._get(f"/panel/api/inbounds/getClientTrafficsById/{inbound_id}")

    async def get_client_ips(self, email: str) -> dict[str, Any]:
        """Get client IP addresses."""
        return await self._post(f"/panel/api/inbounds/clientIps/{email}")

    async def clear_client_ips(self, email: str) -> dict[str, Any]:
        """Clear client IP addresses."""
        return await self._post(f"/panel/api/inbounds/clearClientIps/{email}")

    # ─── Client Management API ────────────────────────────────────────────

    async def add_client(self, inbound_id: int, clients: list[dict[str, Any]]) -> dict[str, Any]:
        """Add client(s) to an inbound."""
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": clients}),
        }
        return await self._post("/panel/api/inbounds/addClient", json=payload)

    async def update_client(self, client_uuid: str, inbound_id: int,
                            client_data: dict[str, Any]) -> dict[str, Any]:
        """Update a client."""
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_data]}),
        }
        return await self._post(f"/panel/api/inbounds/updateClient/{client_uuid}", json=payload)

    async def delete_client(self, inbound_id: int, client_uuid: str) -> dict[str, Any]:
        """Delete a client from an inbound."""
        return await self._post(f"/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}")

    async def delete_client_by_email(self, inbound_id: int, email: str) -> dict[str, Any]:
        """Delete a client by email."""
        return await self._post(f"/panel/api/inbounds/{inbound_id}/delClientByEmail/{email}")

    async def reset_client_traffic(self, inbound_id: int, email: str) -> dict[str, Any]:
        """Reset traffic for a specific client."""
        return await self._post(f"/panel/api/inbounds/{inbound_id}/resetClientTraffic/{email}")

    async def reset_all_traffics(self) -> dict[str, Any]:
        """Reset traffic for all inbounds."""
        return await self._post("/panel/api/inbounds/resetAllTraffics")

    async def reset_all_client_traffics(self, inbound_id: int) -> dict[str, Any]:
        """Reset traffic for all clients in an inbound."""
        return await self._post(f"/panel/api/inbounds/resetAllClientTraffics/{inbound_id}")

    async def delete_depleted_clients(self, inbound_id: int) -> dict[str, Any]:
        """Delete clients with depleted traffic. Use -1 for all inbounds."""
        return await self._post(f"/panel/api/inbounds/delDepletedClients/{inbound_id}")

    async def get_online_clients(self) -> dict[str, Any]:
        """Get currently online clients."""
        return await self._post("/panel/api/inbounds/onlines")

    async def get_last_online(self) -> dict[str, Any]:
        """Get last online time for clients."""
        return await self._post("/panel/api/inbounds/lastOnline")

    async def update_client_traffic(self, email: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update traffic for a specific client."""
        return await self._post(f"/panel/api/inbounds/updateClientTraffic/{email}", json=data)

    async def import_inbound(self, data: dict[str, Any]) -> dict[str, Any]:
        """Import inbound configuration."""
        return await self._post("/panel/api/inbounds/import", json=data)

    # ─── Server API ──────────────────────────────────────────────────────

    async def get_server_status(self) -> dict[str, Any]:
        """Get server resource usage status."""
        return await self._post("/panel/api/server/status")

    async def get_xray_version(self) -> dict[str, Any]:
        """Get available Xray versions."""
        return await self._get("/panel/api/server/getXrayVersion")

    async def get_config_json(self) -> dict[str, Any]:
        """Get the current Xray config.json."""
        return await self._get("/panel/api/server/getConfigJson")

    async def get_db(self) -> bytes:
        """Download the database file."""
        await self._ensure_login()
        session = await self._get_session()
        url = f"{self.base_url}/panel/api/server/getDb"
        async with session.get(url) as resp:
            return await resp.read()

    async def get_new_uuid(self) -> dict[str, Any]:
        """Generate a new UUID."""
        return await self._get("/panel/api/server/getNewUUID")

    async def get_new_x25519(self) -> dict[str, Any]:
        """Generate a new X25519 certificate."""
        return await self._get("/panel/api/server/getNewX25519Cert")

    async def stop_xray(self) -> dict[str, Any]:
        """Stop the Xray service."""
        return await self._post("/panel/api/server/stopXrayService")

    async def restart_xray(self) -> dict[str, Any]:
        """Restart the Xray service."""
        return await self._post("/panel/api/server/restartXrayService")

    async def install_xray(self, version: str) -> dict[str, Any]:
        """Install or update Xray to a specific version."""
        return await self._post(f"/panel/api/server/installXray/{version}")

    async def update_geofiles(self) -> dict[str, Any]:
        """Update GeoIP/GeoSite data files."""
        return await self._post("/panel/api/server/updateGeofile")

    async def get_logs(self, count: int = 50, level: str = "",
                       syslog: str = "") -> dict[str, Any]:
        """Get system logs."""
        params: dict[str, Any] = {}
        if level:
            params["level"] = level
        if syslog:
            params["syslog"] = syslog
        return await self._post(f"/panel/api/server/logs/{count}", json=params)

    async def get_xray_logs(self, count: int = 50) -> dict[str, Any]:
        """Get Xray logs."""
        return await self._post(f"/panel/api/server/xraylogs/{count}")

    async def import_db(self, db_data: bytes) -> dict[str, Any]:
        """Import a database file."""
        await self._ensure_login()
        session = await self._get_session()
        url = f"{self.base_url}/panel/api/server/importDB"
        form = aiohttp.FormData()
        form.add_field("db", db_data, filename="x-ui.db",
                       content_type="application/octet-stream")
        async with session.post(url, data=form) as resp:
            return await self._parse_response(resp)

    # ─── Extra API ───────────────────────────────────────────────────────

    async def backup_to_telegram(self) -> dict[str, Any]:
        """Trigger backup to Telegram bot."""
        return await self._get("/panel/api/backuptotgbot")

    # ─── Cleanup ─────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
