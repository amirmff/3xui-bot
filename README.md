<div align="center">

# 🌐 3x-ui Bot

### Full-Featured Telegram Bot for 3x-ui Panel Management

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![3x-ui](https://img.shields.io/badge/3x--ui-v2.8.11+-green.svg)](https://github.com/MHSanaei/3x-ui)
[![Telegram Bot API](https://img.shields.io/badge/Bot%20API-v7.0+-blue.svg)](https://core.telegram.org/bots/api)

**Manage your entire 3x-ui VPN panel from Telegram — inbounds, clients, server, backups, and more.**

**Multi-panel support** • **Persian UI** • **Proxy support** • **Auto monitoring**

[Installation](#-quick-install) • [Features](#-features) • [Screenshots](#-bot-preview) • [Configuration](#%EF%B8%8F-configuration) • [FAQ](#-faq)

</div>

---

## ⚡ Quick Install

**One-line install** on any Ubuntu/Debian server:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/amirmff/3xui-bot/main/install.sh)
```

Or manually:

```bash
git clone https://github.com/amirmff/3xui-bot.git /opt/3xui-tgbot
cd /opt/3xui-tgbot
chmod +x setup.sh
sudo bash setup.sh
```

The interactive CLI will guide you through installation, configuration, and starting the bot.

---

## ✨ Features

### 🖥 Multi-Panel Management
- Connect and manage **multiple 3x-ui panels** from a single bot
- Add, edit, delete, and switch between panels on the fly
- Each panel has its own URL, credentials, and optional proxy
- Active panel indicator in the main menu

### 📋 Inbound Management
- List, add, edit, and delete inbounds
- Toggle enable/disable
- Support for **VMESS, VLESS, Trojan, Shadowsocks**
- Networks: TCP, WebSocket, gRPC, HTTPUpgrade, SplitHTTP
- Security: None, TLS, Reality

### 👥 Client Management
- Full CRUD (Create, Read, Update, Delete)
- **Add days** to client expiry
- **Add traffic** to client volume
- **Renew** client (reset + new limits)
- **Quick templates** — create clients with pre-configured plans in 2 taps
- Search client by email
- Toggle enable/disable
- Reset traffic, manage IPs

### 🔗 Connection Links & QR Codes
- Generate connection links for all protocols
- Generate scannable QR codes
- Copy-ready formatted output

### 📋 Bulk Operations
- Add days/traffic to **all clients** in an inbound
- Reset all client traffics (per-inbound or global)
- Delete depleted clients

### 🖥 Server Management
- Real-time status (CPU, RAM, Disk, Network)
- Restart / Stop Xray service
- Install specific Xray versions
- Update GeoIP/GeoSite files
- View system and Xray logs
- Generate UUID and X25519 keys

### 💾 Backup & Restore
- Download database backup
- Download Xray config
- Import database
- Backup to Telegram

### ⏰ Automated Monitoring
- **Traffic monitor** — checks every 5 minutes
- **Auto Xray restart** when clients exceed limits
- **Expiry alerts** — warns 24 hours before expiration
- **Periodic status reports** — server health every 6 hours

### 🔌 Proxy Support (Optional)
- SOCKS5 and HTTP proxy support
- Perfect for when the bot runs abroad and panel is in a restricted region
- Configure per-panel — each panel can have its own proxy

### 📱 Dual Keyboard
- **Inline keyboards** for navigation and actions
- **Reply keyboard** (persistent bottom bar) for quick access
- 7 shortcut buttons always visible

### 🌐 Persian (فارسی) Interface
- All messages, buttons, menus, and alerts in Persian
- RTL-friendly formatting

---

## 📸 Bot Preview

### Main Menu
```
🌐 مدیریت پنل 3x-ui

سلام! از منوی زیر برای مدیریت پنل VPN استفاده کنید.

📡 پنل فعال: Main Server

[📋 اینباندها] [👥 کاربران]
[🖥 سرور]     [💾 بکاپ]
[📡 آنلاین‌ها] [🖥 Main Server]
[ℹ️ راهنما]
```

### Reply Keyboard (Always Visible)
```
[📋 اینباندها] [👥 کاربران]
[🖥 سرور]     [💾 بکاپ]
[📡 آنلاین‌ها] [📊 وضعیت]
[🖥 پنل‌ها]
```

---

## 📦 Prerequisites

| Requirement | Version |
|-------------|---------|
| OS | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.10+ |
| 3x-ui Panel | v2.8.11+ |
| Telegram Bot Token | From [@BotFather](https://t.me/BotFather) |

---

## 🛠 CLI Management

After installation, manage the bot using the interactive CLI:

```bash
sudo bash /opt/3xui-tgbot/setup.sh
```

```
╔══════════════════════════════════════════════════╗
║       🌐  3x-ui Telegram Bot Manager  🌐        ║
╚══════════════════════════════════════════════════╝

 Status: ● Running

 Installation
   1)  📦 Install Bot
   2)  ⚙️  Configure Bot
   3)  🔌 Test Connection

 Management
   4)  ▶️  Start Bot
   5)  ⏹  Stop Bot
   6)  🔄 Restart Bot

 Monitoring
   7)  📊 Show Status
   8)  📜 View Logs

 Maintenance
   9)  🔄 Update Bot
   10) 📝 Edit Config File
   11) 🗑  Uninstall
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather | `123456:ABC-DEF` |
| `ADMIN_CHAT_IDS` | ✅ | Comma-separated admin Telegram IDs | `123456789,987654321` |
| `PANEL_URL` | ✅ | 3x-ui panel URL | `https://server.com:2053` |
| `PANEL_USERNAME` | ✅ | Panel login username | `admin` |
| `PANEL_PASSWORD` | ✅ | Panel login password | `your_password` |
| `PANEL_PATH` | ❌ | Custom panel base path | `custom-path` |
| `PROXY_URL` | ❌ | Proxy for panel connection | `socks5://user:pass@ip:port` |
| `TRAFFIC_CHECK_INTERVAL` | ❌ | Traffic check interval (seconds) | `300` (default) |
| `EXPIRY_CHECK_INTERVAL` | ❌ | Expiry check interval (seconds) | `3600` (default) |
| `ENABLE_AUTO_RESTART` | ❌ | Auto restart Xray on traffic exceed | `true` (default) |

### Multi-Panel Setup

Panels are managed directly through the bot interface:

1. Open the bot → Main Menu → 🖥 Panels
2. Click **➕ Add Panel**
3. Follow the 6-step wizard (name, URL, username, password, path, proxy)
4. Click **🟢 Switch to This Panel** to activate

The first panel is auto-created from your `.env` configuration. Additional panels are stored in `panels.json`.

---

## 🏗 Project Structure

```
3xui-bot/
├── bot.py                  # Entry point — multi-panel boot
├── config.py               # Environment configuration
├── lang.py                 # Persian language strings (200+)
├── panels.py               # Multi-panel storage manager
├── scheduler.py            # Cron jobs (traffic, expiry, status)
├── requirements.txt        # Python dependencies
├── setup.sh                # Interactive CLI installer
├── install.sh              # One-liner quick install
├── .env.example            # Configuration template
├── .gitignore
├── LICENSE
├── README.md
│
├── api/
│   ├── __init__.py
│   ├── client.py           # Async HTTP client with proxy support
│   └── models.py           # Data models
│
├── handlers/
│   ├── __init__.py
│   ├── common.py           # Shared utilities & keyboards
│   ├── start.py            # Main menu & reply keyboard
│   ├── inbounds.py         # Inbound CRUD handlers
│   ├── clients.py          # Client management (65KB!)
│   ├── server.py           # Server monitoring handlers
│   ├── backup.py           # Backup & restore handlers
│   └── panels.py           # Multi-panel management
│
└── utils/
    ├── __init__.py
    ├── formatters.py        # Message formatting
    └── helpers.py           # Links, QR, UUID generation
```

---

## 🔒 Security

- **Admin-only access** — only specified Telegram IDs can use the bot
- **Credentials stored in `.env`** with `600` permissions (root only)
- **Session cookies** stored in memory only
- **No data logging** — bot doesn't store user data
- **Password masking** in panel view

---

## 📋 Quick Templates

Pre-configured client plans for fast creation:

| Template | Days | Traffic | IP Limit |
|----------|------|---------|----------|
| 🟢 1 Month 50GB | 30 | 50 GB | 2 |
| 🔵 1 Month 100GB | 30 | 100 GB | 3 |
| 🟡 3 Months 150GB | 90 | 150 GB | 2 |
| 🟣 6 Months 300GB | 180 | 300 GB | 3 |
| 🔴 Unlimited 1 Month | 30 | ♾ | 2 |

Customize templates in [`lang.py`](lang.py) → `TEMPLATES` list.

---

## 🔄 Updating

```bash
cd /opt/3xui-tgbot
sudo bash setup.sh
# Choose option 9 (Update Bot)
```

Or manually:
```bash
cd /opt/3xui-tgbot
git pull
sudo bash setup.sh
# Choose option 6 (Restart Bot)
```

---

## ❓ FAQ

<details>
<summary><b>How do I get my Telegram Chat ID?</b></summary>

Send a message to [@userinfobot](https://t.me/userinfobot) on Telegram. It will reply with your Chat ID.
</details>

<details>
<summary><b>Can I manage panels in different countries?</b></summary>

Yes! Each panel can have its own proxy configuration. Set a SOCKS5 or HTTP proxy per panel if the bot can't reach the panel directly.
</details>

<details>
<summary><b>Is proxy required?</b></summary>

No, proxy is completely optional. Only configure it if your bot server cannot directly reach the panel server.
</details>

<details>
<summary><b>How to add multiple admins?</b></summary>

Set `ADMIN_CHAT_IDS` to a comma-separated list: `123456789,987654321,111222333`
</details>

<details>
<summary><b>What happens if the bot restarts?</b></summary>

The systemd service auto-restarts the bot. Panel configurations are persisted in `panels.json`. Session cookies are re-established automatically.
</details>

<details>
<summary><b>Can I customize the quick templates?</b></summary>

Yes! Edit the `TEMPLATES` list in `lang.py` to add/modify/remove plans.
</details>

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [3x-ui](https://github.com/MHSanaei/3x-ui) — The amazing panel this bot manages
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — Telegram Bot framework
- [Xray-core](https://github.com/XTLS/Xray-core) — The proxy engine

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the community

</div>
