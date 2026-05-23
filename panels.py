"""Multi-panel manager — stores panel configs in JSON file."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

PANELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panels.json")


class Panel:
    """Represents a single 3x-ui panel configuration."""

    def __init__(self, id: str, name: str, url: str, username: str = "admin",
                 password: str = "admin", path: str = "", proxy_url: str = ""):
        self.id = id
        self.name = name
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.path = path.strip("/")
        self.proxy_url = proxy_url

    @property
    def api_base(self) -> str:
        if self.path:
            return f"{self.url}/{self.path}"
        return self.url

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "path": self.path,
            "proxy_url": self.proxy_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Panel":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            username=data.get("username", "admin"),
            password=data.get("password", "admin"),
            path=data.get("path", ""),
            proxy_url=data.get("proxy_url", ""),
        )


class PanelManager:
    """Manages multiple 3x-ui panel configurations."""

    def __init__(self, filepath: str = PANELS_FILE):
        self.filepath = filepath
        self._panels: dict[str, Panel] = {}
        self._load()

    def _load(self) -> None:
        """Load panels from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("panels", []):
                    panel = Panel.from_dict(p)
                    self._panels[panel.id] = panel
                logger.info("Loaded %d panel(s) from %s", len(self._panels), self.filepath)
            except Exception as e:
                logger.error("Error loading panels: %s", e)
        else:
            logger.info("No panels.json found, will create on first panel add")

    def _save(self) -> None:
        """Save panels to JSON file."""
        data = {
            "panels": [p.to_dict() for p in self._panels.values()]
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving panels: %s", e)

    def add_panel(self, panel: Panel) -> None:
        """Add or update a panel."""
        self._panels[panel.id] = panel
        self._save()

    def remove_panel(self, panel_id: str) -> bool:
        """Remove a panel by ID."""
        if panel_id in self._panels:
            del self._panels[panel_id]
            self._save()
            return True
        return False

    def get_panel(self, panel_id: str) -> Optional[Panel]:
        """Get a panel by ID."""
        return self._panels.get(panel_id)

    def get_all_panels(self) -> list[Panel]:
        """Get all panels."""
        return list(self._panels.values())

    def count(self) -> int:
        return len(self._panels)

    def generate_id(self) -> str:
        """Generate a unique panel ID."""
        i = 1
        while f"panel_{i}" in self._panels:
            i += 1
        return f"panel_{i}"

    def ensure_default_panel(self, url: str, username: str, password: str,
                              path: str = "", proxy_url: str = "") -> Panel:
        """
        Ensure there's at least one panel (from .env config).
        Called on startup if no panels exist.
        """
        if not self._panels and url:
            panel = Panel(
                id="default",
                name="Default Panel",
                url=url,
                username=username,
                password=password,
                path=path,
                proxy_url=proxy_url,
            )
            self.add_panel(panel)
            logger.info("Created default panel from .env config")
            return panel
        return next(iter(self._panels.values())) if self._panels else None
