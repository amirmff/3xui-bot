#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3x-ui Telegram Bot — Installer & Management Script
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Ensure stdin comes from terminal (fixes curl | bash piping)
if [ -t 0 ]; then
    : # Already running from terminal
else
    exec < /dev/tty
fi

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# ── Paths ─────────────────────────────────────────────────────
INSTALL_DIR="/opt/3xui-tgbot"
SERVICE_NAME="3xui-tgbot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_FILE="${INSTALL_DIR}/.env"
VENV_DIR="${INSTALL_DIR}/venv"
LOG_FILE="/var/log/${SERVICE_NAME}.log"

# ── Helpers ───────────────────────────────────────────────────
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║                                                  ║"
    echo "  ║       🌐  3x-ui Telegram Bot Manager  🌐        ║"
    echo "  ║                                                  ║"
    echo "  ║       Full Panel Management via Telegram         ║"
    echo "  ║                                                  ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_line() {
    echo -e "${GRAY}  ──────────────────────────────────────────────────${NC}"
}

print_status() {
    echo -e "  ${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "  ${RED}❌${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}⚠️${NC}  $1"
}

print_info() {
    echo -e "  ${BLUE}ℹ️${NC}  $1"
}

press_enter() {
    echo ""
    echo -e "  ${DIM}Press Enter to continue...${NC}"
    read -r
}

# ── Check Root ────────────────────────────────────────────────
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# ── Check if installed ────────────────────────────────────────
is_installed() {
    [[ -d "$INSTALL_DIR" && -f "${INSTALL_DIR}/bot.py" ]]
}

is_service_active() {
    systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null
}

is_service_enabled() {
    systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null
}

get_service_status() {
    if is_service_active; then
        echo -e "${GREEN}● Running${NC}"
    elif is_installed; then
        echo -e "${RED}● Stopped${NC}"
    else
        echo -e "${GRAY}● Not Installed${NC}"
    fi
}

# ── Install Dependencies ─────────────────────────────────────
install_dependencies() {
    print_info "Installing system dependencies..."
    echo ""

    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq python3 python3-pip python3-venv curl wget > /dev/null 2>&1

    print_status "Python3 installed"
    print_status "pip3 installed"
    print_status "venv installed"
}

# ── Install Bot ───────────────────────────────────────────────
install_bot() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}📦 Installation${NC}"
    print_line
    echo ""

    if is_installed; then
        print_warning "Bot is already installed at ${INSTALL_DIR}"
        echo ""
        echo -e "  ${YELLOW}Do you want to reinstall? (y/n)${NC}"
        read -r -p "  > " choice
        if [[ "$choice" != "y" && "$choice" != "Y" ]]; then
            return
        fi
        # Stop service if running
        if is_service_active; then
            systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        fi
    fi

    install_dependencies

    echo ""
    print_info "Creating bot directory..."
    mkdir -p "$INSTALL_DIR"

    # Copy bot files (assumes script is in the same dir as bot files)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ -f "${SCRIPT_DIR}/bot.py" ]]; then
        print_info "Copying bot files from ${SCRIPT_DIR}..."
        # Copy all Python files and directories
        cp -r "${SCRIPT_DIR}/bot.py" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/config.py" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/lang.py" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/scheduler.py" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/requirements.txt" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/.env.example" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/api" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/handlers" "$INSTALL_DIR/"
        cp -r "${SCRIPT_DIR}/utils" "$INSTALL_DIR/"
        [[ -f "${SCRIPT_DIR}/README.md" ]] && cp "${SCRIPT_DIR}/README.md" "$INSTALL_DIR/"
    else
        print_error "Bot files not found in ${SCRIPT_DIR}"
        print_info "Make sure setup.sh is in the same directory as bot.py"
        press_enter
        return
    fi

    print_status "Bot files copied"

    # Create virtual environment
    echo ""
    print_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created"

    # Install Python dependencies
    print_info "Installing Python packages..."
    "${VENV_DIR}/bin/pip" install --upgrade pip -q > /dev/null 2>&1
    "${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt" -q > /dev/null 2>&1
    print_status "Python packages installed"

    # Create .env if not exists
    if [[ ! -f "$ENV_FILE" ]]; then
        cp "${INSTALL_DIR}/.env.example" "$ENV_FILE"
        print_info ".env file created (needs configuration)"
    fi

    # Create systemd service
    create_service

    echo ""
    print_line
    print_status "Installation complete!"
    echo ""
    print_warning "You need to configure the bot before starting."
    print_info "Use option 2 from the main menu to configure."
    press_enter
}

# ── Create Systemd Service ────────────────────────────────────
create_service() {
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=3x-ui Telegram Management Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${VENV_DIR}/bin/python ${INSTALL_DIR}/bot.py
Restart=always
RestartSec=5
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

# Environment
EnvironmentFile=${ENV_FILE}

# Security
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=${INSTALL_DIR}

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
    print_status "Systemd service created and enabled"
}

# ── Configure Bot ─────────────────────────────────────────────
configure_bot() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}⚙️  Configuration${NC}"
    print_line
    echo ""

    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "${INSTALL_DIR}/.env.example" ]]; then
            cp "${INSTALL_DIR}/.env.example" "$ENV_FILE"
        else
            print_error ".env file not found. Install the bot first."
            press_enter
            return
        fi
    fi

    # Read current values
    source "$ENV_FILE" 2>/dev/null || true

    echo -e "  ${WHITE}Current configuration:${NC}"
    echo -e "  ${GRAY}(Press Enter to keep current value)${NC}"
    echo ""

    # Telegram Bot Token
    local current_token="${TELEGRAM_BOT_TOKEN:-not set}"
    local display_token="not set"
    if [[ "$current_token" != "not set" && "$current_token" != "your_bot_token_here" ]]; then
        display_token="${current_token:0:10}...${current_token: -5}"
    fi
    echo -e "  ${CYAN}1. Telegram Bot Token${NC} ${GRAY}[${display_token}]${NC}"
    echo -e "     ${DIM}Get from @BotFather on Telegram${NC}"
    read -r -p "     > " new_token
    [[ -n "$new_token" ]] && TELEGRAM_BOT_TOKEN="$new_token"

    echo ""

    # Panel URL
    echo -e "  ${CYAN}2. Panel URL${NC} ${GRAY}[${PANEL_URL:-not set}]${NC}"
    echo -e "     ${DIM}Example: https://your-server.com:2053${NC}"
    read -r -p "     > " new_url
    [[ -n "$new_url" ]] && PANEL_URL="$new_url"

    echo ""

    # Panel Username
    echo -e "  ${CYAN}3. Panel Username${NC} ${GRAY}[${PANEL_USERNAME:-admin}]${NC}"
    read -r -p "     > " new_user
    [[ -n "$new_user" ]] && PANEL_USERNAME="$new_user"

    echo ""

    # Panel Password
    local display_pass="not set"
    if [[ -n "$PANEL_PASSWORD" && "$PANEL_PASSWORD" != "admin" ]]; then
        display_pass="****"
    fi
    echo -e "  ${CYAN}4. Panel Password${NC} ${GRAY}[${display_pass}]${NC}"
    read -r -s -p "     > " new_pass
    echo ""
    [[ -n "$new_pass" ]] && PANEL_PASSWORD="$new_pass"

    echo ""

    # Admin Chat IDs
    echo -e "  ${CYAN}5. Admin Telegram Chat IDs${NC} ${GRAY}[${ADMIN_CHAT_IDS:-not set}]${NC}"
    echo -e "     ${DIM}Comma-separated. Get your ID from @userinfobot${NC}"
    read -r -p "     > " new_ids
    [[ -n "$new_ids" ]] && ADMIN_CHAT_IDS="$new_ids"

    echo ""

    # Panel Path
    echo -e "  ${CYAN}6. Panel Base Path${NC} ${GRAY}[${PANEL_PATH:-empty}]${NC}"
    echo -e "     ${DIM}Leave empty if default. Example: custom-path${NC}"
    read -r -p "     > " new_path
    [[ -n "$new_path" ]] && PANEL_PATH="$new_path"

    echo ""

    # Proxy
    echo -e "  ${CYAN}7. Proxy URL (optional)${NC} ${GRAY}[${PROXY_URL:-none}]${NC}"
    echo -e "     ${DIM}For when bot is abroad, panel in Iran${NC}"
    echo -e "     ${DIM}Examples: socks5://user:pass@ip:port, http://ip:port${NC}"
    read -r -p "     > " new_proxy
    if [[ -n "$new_proxy" ]]; then
        PROXY_URL="$new_proxy"
    fi

    echo ""
    print_line
    echo ""

    # Advanced settings
    echo -e "  ${YELLOW}Configure advanced settings? (y/n)${NC} ${GRAY}[n]${NC}"
    read -r -p "  > " advanced
    if [[ "$advanced" == "y" || "$advanced" == "Y" ]]; then
        echo ""
        echo -e "  ${CYAN}8. Traffic Check Interval (seconds)${NC} ${GRAY}[${TRAFFIC_CHECK_INTERVAL:-300}]${NC}"
        read -r -p "     > " new_interval
        [[ -n "$new_interval" ]] && TRAFFIC_CHECK_INTERVAL="$new_interval"

        echo ""
        echo -e "  ${CYAN}9. Expiry Check Interval (seconds)${NC} ${GRAY}[${EXPIRY_CHECK_INTERVAL:-3600}]${NC}"
        read -r -p "     > " new_expiry_int
        [[ -n "$new_expiry_int" ]] && EXPIRY_CHECK_INTERVAL="$new_expiry_int"

        echo ""
        echo -e "  ${CYAN}10. Auto Restart Xray on traffic exceed${NC} ${GRAY}[${ENABLE_AUTO_RESTART:-true}]${NC}"
        echo -e "     ${DIM}true/false${NC}"
        read -r -p "      > " new_auto
        [[ -n "$new_auto" ]] && ENABLE_AUTO_RESTART="$new_auto"
    fi

    # Write .env file
    cat > "$ENV_FILE" << EOF
# 3x-ui Telegram Bot Configuration
# Generated by setup.sh

TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-your_bot_token_here}
PANEL_URL=${PANEL_URL:-https://your-server.com:2053}
PANEL_USERNAME=${PANEL_USERNAME:-admin}
PANEL_PASSWORD=${PANEL_PASSWORD:-admin}
ADMIN_CHAT_IDS=${ADMIN_CHAT_IDS:-123456789}
PANEL_PATH=${PANEL_PATH:-}
PROXY_URL=${PROXY_URL:-}
TRAFFIC_CHECK_INTERVAL=${TRAFFIC_CHECK_INTERVAL:-300}
EXPIRY_CHECK_INTERVAL=${EXPIRY_CHECK_INTERVAL:-3600}
ENABLE_AUTO_RESTART=${ENABLE_AUTO_RESTART:-true}
EOF

    chmod 600 "$ENV_FILE"

    echo ""
    print_status "Configuration saved to ${ENV_FILE}"
    print_info "File permissions set to 600 (owner only)"

    if is_service_active; then
        echo ""
        echo -e "  ${YELLOW}Restart bot to apply changes? (y/n)${NC}"
        read -r -p "  > " restart
        if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
            systemctl restart "$SERVICE_NAME"
            sleep 2
            if is_service_active; then
                print_status "Bot restarted successfully"
            else
                print_error "Bot failed to start. Check logs."
            fi
        fi
    fi

    press_enter
}

# ── Start Bot ─────────────────────────────────────────────────
start_bot() {
    if ! is_installed; then
        print_error "Bot is not installed. Install first."
        press_enter
        return
    fi

    if is_service_active; then
        print_warning "Bot is already running"
        press_enter
        return
    fi

    # Validate config
    if grep -q "your_bot_token_here" "$ENV_FILE" 2>/dev/null; then
        print_error "Bot token not configured! Use option 2 to configure."
        press_enter
        return
    fi

    systemctl start "$SERVICE_NAME"
    sleep 2

    if is_service_active; then
        print_status "Bot started successfully! ✨"
    else
        print_error "Bot failed to start. Showing last logs:"
        echo ""
        journalctl -u "$SERVICE_NAME" --no-pager -n 10
    fi
    press_enter
}

# ── Stop Bot ──────────────────────────────────────────────────
stop_bot() {
    if ! is_service_active; then
        print_warning "Bot is not running"
        press_enter
        return
    fi

    systemctl stop "$SERVICE_NAME"
    print_status "Bot stopped"
    press_enter
}

# ── Restart Bot ───────────────────────────────────────────────
restart_bot() {
    if ! is_installed; then
        print_error "Bot is not installed"
        press_enter
        return
    fi

    systemctl restart "$SERVICE_NAME"
    sleep 2

    if is_service_active; then
        print_status "Bot restarted successfully!"
    else
        print_error "Bot failed to restart. Check logs."
    fi
    press_enter
}

# ── View Logs ─────────────────────────────────────────────────
view_logs() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}📜 Bot Logs${NC}"
    print_line
    echo ""
    echo -e "  ${GRAY}Showing last 50 lines (Ctrl+C to exit)${NC}"
    echo ""

    if [[ -f "$LOG_FILE" ]]; then
        tail -50 "$LOG_FILE"
    else
        journalctl -u "$SERVICE_NAME" --no-pager -n 50
    fi

    echo ""
    print_line
    echo ""
    echo -e "  ${CYAN}Options:${NC}"
    echo -e "    ${WHITE}1${NC}) Follow live logs"
    echo -e "    ${WHITE}2${NC}) Show all logs"
    echo -e "    ${WHITE}3${NC}) Clear logs"
    echo -e "    ${WHITE}0${NC}) Back"
    echo ""
    read -r -p "  > " log_choice

    case "$log_choice" in
        1)
            echo -e "  ${GRAY}Following logs... (Ctrl+C to stop)${NC}"
            if [[ -f "$LOG_FILE" ]]; then
                tail -f "$LOG_FILE"
            else
                journalctl -u "$SERVICE_NAME" -f
            fi
            ;;
        2)
            if [[ -f "$LOG_FILE" ]]; then
                less "$LOG_FILE"
            else
                journalctl -u "$SERVICE_NAME" --no-pager | less
            fi
            ;;
        3)
            if [[ -f "$LOG_FILE" ]]; then
                > "$LOG_FILE"
                print_status "Logs cleared"
            fi
            press_enter
            ;;
    esac
}

# ── Show Status ───────────────────────────────────────────────
show_status() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}📊 Bot Status${NC}"
    print_line
    echo ""

    # Service status
    echo -e "  ${WHITE}Service:${NC}     $(get_service_status)"

    if is_installed; then
        echo -e "  ${WHITE}Install Dir:${NC} ${GRAY}${INSTALL_DIR}${NC}"
        echo -e "  ${WHITE}Service:${NC}     ${GRAY}${SERVICE_NAME}${NC}"

        if [[ -f "$ENV_FILE" ]]; then
            source "$ENV_FILE" 2>/dev/null || true
            echo ""
            echo -e "  ${WHITE}Panel URL:${NC}   ${GRAY}${PANEL_URL:-not set}${NC}"
            echo -e "  ${WHITE}Username:${NC}    ${GRAY}${PANEL_USERNAME:-not set}${NC}"
            echo -e "  ${WHITE}Admin IDs:${NC}   ${GRAY}${ADMIN_CHAT_IDS:-not set}${NC}"

            if [[ -n "$PROXY_URL" ]]; then
                local proxy_display="${PROXY_URL}"
                if [[ "$proxy_display" == *"@"* ]]; then
                    proxy_display="${proxy_display##*@}"
                    proxy_display="***@${proxy_display}"
                fi
                echo -e "  ${WHITE}Proxy:${NC}       ${GRAY}${proxy_display}${NC}"
            else
                echo -e "  ${WHITE}Proxy:${NC}       ${GRAY}none${NC}"
            fi

            echo -e "  ${WHITE}Auto Restart:${NC}${GRAY} ${ENABLE_AUTO_RESTART:-true}${NC}"
            echo -e "  ${WHITE}Traffic Chk:${NC} ${GRAY}every ${TRAFFIC_CHECK_INTERVAL:-300}s${NC}"
        fi

        # Memory usage
        if is_service_active; then
            echo ""
            local pid=$(systemctl show -p MainPID "$SERVICE_NAME" | cut -d= -f2)
            if [[ "$pid" -gt 0 ]]; then
                local mem=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
                local uptime_val=$(ps -p "$pid" -o etime= 2>/dev/null | xargs)
                echo -e "  ${WHITE}PID:${NC}         ${GRAY}${pid}${NC}"
                echo -e "  ${WHITE}Memory:${NC}      ${GRAY}${mem}${NC}"
                echo -e "  ${WHITE}Uptime:${NC}      ${GRAY}${uptime_val}${NC}"
            fi
        fi
    else
        echo ""
        print_warning "Bot is not installed"
    fi

    echo ""
    print_line
    press_enter
}

# ── Update Bot ────────────────────────────────────────────────
update_bot() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}🔄 Update Bot${NC}"
    print_line
    echo ""

    if ! is_installed; then
        print_error "Bot is not installed"
        press_enter
        return
    fi

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ ! -f "${SCRIPT_DIR}/bot.py" ]]; then
        print_error "New bot files not found in ${SCRIPT_DIR}"
        print_info "Place updated files alongside this script and run update again."
        press_enter
        return
    fi

    # Backup current .env
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "${ENV_FILE}.bak"
        print_status "Configuration backed up"
    fi

    # Stop if running
    local was_running=false
    if is_service_active; then
        was_running=true
        systemctl stop "$SERVICE_NAME"
        print_status "Bot stopped for update"
    fi

    # Copy new files
    print_info "Copying updated files..."
    cp -r "${SCRIPT_DIR}/bot.py" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/config.py" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/lang.py" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/scheduler.py" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/requirements.txt" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/api" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/handlers" "$INSTALL_DIR/"
    cp -r "${SCRIPT_DIR}/utils" "$INSTALL_DIR/"
    print_status "Files updated"

    # Reinstall packages
    print_info "Updating Python packages..."
    "${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt" -q > /dev/null 2>&1
    print_status "Packages updated"

    # Restore .env
    if [[ -f "${ENV_FILE}.bak" && ! -f "$ENV_FILE" ]]; then
        cp "${ENV_FILE}.bak" "$ENV_FILE"
    fi

    # Restart if was running
    if $was_running; then
        systemctl start "$SERVICE_NAME"
        sleep 2
        if is_service_active; then
            print_status "Bot restarted!"
        else
            print_error "Bot failed to start after update"
        fi
    fi

    echo ""
    print_status "Update complete!"
    press_enter
}

# ── Uninstall ─────────────────────────────────────────────────
uninstall_bot() {
    print_banner
    echo -e "  ${RED}${BOLD}🗑  Uninstall${NC}"
    print_line
    echo ""

    if ! is_installed; then
        print_warning "Bot is not installed"
        press_enter
        return
    fi

    echo -e "  ${RED}Are you sure you want to uninstall? (type YES to confirm)${NC}"
    read -r -p "  > " confirm

    if [[ "$confirm" != "YES" ]]; then
        print_info "Uninstall cancelled"
        press_enter
        return
    fi

    # Stop and disable service
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload

    print_status "Service removed"

    # Ask to keep config
    echo ""
    echo -e "  ${YELLOW}Keep configuration file (.env)? (y/n)${NC}"
    read -r -p "  > " keep_conf

    if [[ "$keep_conf" == "y" || "$keep_conf" == "Y" ]]; then
        cp "$ENV_FILE" "/root/3xui-bot.env.bak" 2>/dev/null || true
        print_info "Config saved to /root/3xui-bot.env.bak"
    fi

    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -f "$LOG_FILE"

    print_status "Bot uninstalled"
    press_enter
}

# ── Edit Config File ──────────────────────────────────────────
edit_config_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found"
        press_enter
        return
    fi

    # Try to use nano, fall back to vi
    if command -v nano &> /dev/null; then
        nano "$ENV_FILE"
    elif command -v vi &> /dev/null; then
        vi "$ENV_FILE"
    else
        print_error "No text editor found (nano/vi)"
        press_enter
    fi
}

# ── Test Connection ───────────────────────────────────────────
test_connection() {
    print_banner
    echo -e "  ${PURPLE}${BOLD}🔌 Connection Test${NC}"
    print_line
    echo ""

    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Config not found. Configure first."
        press_enter
        return
    fi

    source "$ENV_FILE" 2>/dev/null || true

    if [[ -z "$PANEL_URL" || "$PANEL_URL" == "https://your-server.com:2053" ]]; then
        print_error "Panel URL not configured"
        press_enter
        return
    fi

    print_info "Testing connection to panel..."
    echo ""

    # Test direct connection
    if curl -sk --connect-timeout 10 "${PANEL_URL}" > /dev/null 2>&1; then
        print_status "Direct connection to panel: OK"
    else
        print_error "Direct connection to panel: FAILED"

        if [[ -n "$PROXY_URL" ]]; then
            print_info "Testing via proxy..."
            local proxy_flag=""
            if [[ "$PROXY_URL" == socks5://* ]]; then
                proxy_flag="--socks5 ${PROXY_URL#socks5://}"
            else
                proxy_flag="--proxy ${PROXY_URL}"
            fi

            if curl -sk --connect-timeout 10 $proxy_flag "${PANEL_URL}" > /dev/null 2>&1; then
                print_status "Connection via proxy: OK"
            else
                print_error "Connection via proxy: FAILED"
            fi
        fi
    fi

    # Test Telegram API
    echo ""
    print_info "Testing Telegram API..."
    if [[ -n "$TELEGRAM_BOT_TOKEN" && "$TELEGRAM_BOT_TOKEN" != "your_bot_token_here" ]]; then
        local tg_result=$(curl -sk --connect-timeout 10 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" 2>/dev/null)
        if echo "$tg_result" | grep -q '"ok":true'; then
            local bot_name=$(echo "$tg_result" | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
            local bot_username=$(echo "$tg_result" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
            print_status "Telegram Bot: @${bot_username} (${bot_name})"
        else
            print_error "Telegram Bot token is invalid"
        fi
    else
        print_warning "Bot token not configured"
    fi

    echo ""
    # Test login to panel
    print_info "Testing panel login..."
    if [[ -n "$PANEL_URL" && -n "$PANEL_USERNAME" ]]; then
        # Build proxy flags for curl
        local curl_proxy=""
        if [[ -n "$PROXY_URL" ]]; then
            if [[ "$PROXY_URL" == socks5://* ]]; then
                curl_proxy="--socks5-hostname ${PROXY_URL#socks5://}"
            elif [[ "$PROXY_URL" == socks5h://* ]]; then
                curl_proxy="--socks5-hostname ${PROXY_URL#socks5h://}"
            else
                curl_proxy="--proxy ${PROXY_URL}"
            fi
        fi

        # Try login with panel path if set
        local login_url="${PANEL_URL}/login"
        if [[ -n "$PANEL_PATH" ]]; then
            login_url="${PANEL_URL}/${PANEL_PATH}/login"
        fi

        local login_result=$(curl -sk --connect-timeout 15 $curl_proxy \
            -X POST "${login_url}" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "username=${PANEL_USERNAME}&password=${PANEL_PASSWORD}" 2>/dev/null)

        if echo "$login_result" | grep -q '"success":true'; then
            print_status "Panel login: OK"
        else
            # Try JSON format too
            login_result=$(curl -sk --connect-timeout 15 $curl_proxy \
                -X POST "${login_url}" \
                -H "Content-Type: application/json" \
                -d "{\"username\":\"${PANEL_USERNAME}\",\"password\":\"${PANEL_PASSWORD}\"}" 2>/dev/null)

            if echo "$login_result" | grep -q '"success":true'; then
                print_status "Panel login: OK"
            else
                print_error "Panel login: FAILED"
                local msg=$(echo "$login_result" | grep -o '"msg":"[^"]*"' | cut -d'"' -f4)
                [[ -n "$msg" ]] && print_error "  Message: $msg"
            fi
        fi
    fi

    press_enter
}

# ── Main Menu ─────────────────────────────────────────────────
main_menu() {
    while true; do
        print_banner

        local status=$(get_service_status)
        echo -e "  Status: ${status}"
        print_line
        echo ""

        echo -e "  ${WHITE}${BOLD}Installation${NC}"
        echo -e "    ${CYAN}1${NC})  📦 Install Bot"
        echo -e "    ${CYAN}2${NC})  ⚙️  Configure Bot"
        echo -e "    ${CYAN}3${NC})  🔌 Test Connection"
        echo ""
        echo -e "  ${WHITE}${BOLD}Management${NC}"
        echo -e "    ${CYAN}4${NC})  ▶️  Start Bot"
        echo -e "    ${CYAN}5${NC})  ⏹  Stop Bot"
        echo -e "    ${CYAN}6${NC})  🔄 Restart Bot"
        echo ""
        echo -e "  ${WHITE}${BOLD}Monitoring${NC}"
        echo -e "    ${CYAN}7${NC})  📊 Show Status"
        echo -e "    ${CYAN}8${NC})  📜 View Logs"
        echo ""
        echo -e "  ${WHITE}${BOLD}Maintenance${NC}"
        echo -e "    ${CYAN}9${NC})  🔄 Update Bot"
        echo -e "    ${CYAN}10${NC}) 📝 Edit Config File"
        echo -e "    ${CYAN}11${NC}) 🗑  Uninstall"
        echo ""
        echo -e "    ${CYAN}0${NC})  🚪 Exit"
        echo ""
        print_line
        read -r -p "  Choose an option: " choice

        case "$choice" in
            1) install_bot ;;
            2) configure_bot ;;
            3) test_connection ;;
            4) start_bot ;;
            5) stop_bot ;;
            6) restart_bot ;;
            7) show_status ;;
            8) view_logs ;;
            9) update_bot ;;
            10) edit_config_file ;;
            11) uninstall_bot ;;
            0)
                echo ""
                echo -e "  ${GREEN}Goodbye! 👋${NC}"
                echo ""
                exit 0
                ;;
            *)
                print_error "Invalid option"
                sleep 1
                ;;
        esac
    done
}

# ── Entry Point ───────────────────────────────────────────────
check_root
main_menu
