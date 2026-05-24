#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3x-ui Bot — Quick Install
#
# Usage:
#   bash <(curl -sSL https://raw.githubusercontent.com/amirmff/3xui-bot/main/install.sh)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Don't use set -e — we handle errors manually

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="/opt/3xui-tgbot"
REPO_URL="https://github.com/amirmff/3xui-bot.git"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🌐 3x-ui Telegram Bot — Quick Install ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}❌ Run as root: sudo bash install.sh${NC}"
    exit 1
fi

# Ensure stdin comes from terminal (fixes curl | bash piping)
if [ ! -t 0 ]; then
    exec < /dev/tty
fi

# Install git if needed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Installing git...${NC}"
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq git > /dev/null 2>&1
fi

# Clone repo
if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "${YELLOW}⚠️  ${INSTALL_DIR} already exists${NC}"
    echo -e "    Update existing installation? (y/n)"
    read -r choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        cd "$INSTALL_DIR"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
        echo -e "${GREEN}✅ Updated!${NC}"
    else
        echo "Launching management menu..."
    fi
    chmod +x "${INSTALL_DIR}/setup.sh"
    bash "${INSTALL_DIR}/setup.sh"
    exit 0
fi

echo -e "${GREEN}📥 Downloading 3xui-bot...${NC}"
git clone "$REPO_URL" "$INSTALL_DIR" 2>&1 | tail -1 || {
    echo -e "${RED}❌ Failed to clone repository${NC}"
    echo -e "${YELLOW}   Check: ${REPO_URL}${NC}"
    exit 1
}

echo -e "${GREEN}✅ Downloaded successfully!${NC}"
echo ""

# Run setup
chmod +x "${INSTALL_DIR}/setup.sh"
cd "$INSTALL_DIR"
bash setup.sh
