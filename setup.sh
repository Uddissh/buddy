#!/usr/bin/env bash
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗   ██╗"
echo "  ██╔══██╗██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝"
echo "  ██████╔╝██║   ██║██║  ██║██║  ██║ ╚████╔╝ "
echo "  ██╔══██╗██║   ██║██║  ██║██║  ██║  ╚██╔╝  "
echo "  ██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║   "
echo "  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝   "
echo -e "${NC}"
echo "  Your Terminal AI Companion — Setup"
echo "  ─────────────────────────────────"
echo ""

# ── Collect config ─────────────────────────────────────────────────────────────

read -p "  Hermes IP address (Ollama server) [e.g. 192.168.1.100]: " HERMES_IP
if [[ -z "$HERMES_IP" ]]; then
  echo -e "${RED}  ✗ Hermes IP is required.${NC}"
  exit 1
fi

read -p "  Hermes port [default: 11434]: " HERMES_PORT
HERMES_PORT="${HERMES_PORT:-11434}"

read -p "  Your name [default: User]: " USER_NAME
USER_NAME="${USER_NAME:-User}"

read -p "  Ollama model [default: gemma3:4b]: " MODEL
MODEL="${MODEL:-gemma3:4b}"

echo ""

# ── Create ~/.buddy directory ──────────────────────────────────────────────────

BUDDY_DIR="$HOME/.buddy"
mkdir -p "$BUDDY_DIR/logs"
echo -e "  ${GREEN}✓${NC} Created $BUDDY_DIR"

# ── Write config ───────────────────────────────────────────────────────────────

cat > "$BUDDY_DIR/config.json" << EOF
{
  "hermes_ip":   "$HERMES_IP",
  "hermes_port": $HERMES_PORT,
  "model":       "$MODEL",
  "name":        "Buddy",
  "user_name":   "$USER_NAME",
  "max_history": 20,
  "stream":      true
}
EOF
echo -e "  ${GREEN}✓${NC} Config written to $BUDDY_DIR/config.json"

# ── Python check ───────────────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
  echo -e "  ${RED}✗ python3 not found. Install Python 3.10+${NC}"
  exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  ${GREEN}✓${NC} Python $PY_VER detected"

# ── Install pip deps ───────────────────────────────────────────────────────────

echo ""
echo -e "  ${CYAN}Installing Python dependencies…${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip install --user -q -r "$SCRIPT_DIR/requirements.txt"
echo -e "  ${GREEN}✓${NC} Dependencies installed"

# ── Create launcher ────────────────────────────────────────────────────────────

LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

cat > "$LOCAL_BIN/buddy" << SCRIPT
#!/usr/bin/env bash
python3 "$SCRIPT_DIR/buddy.py" "\$@"
SCRIPT

chmod +x "$LOCAL_BIN/buddy"
echo -e "  ${GREEN}✓${NC} Launcher created at $LOCAL_BIN/buddy"

# ── PATH check ─────────────────────────────────────────────────────────────────

if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
  for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [[ -f "$RC" ]]; then
      echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
      echo -e "  ${YELLOW}⚠${NC}  Added ~/.local/bin to PATH in $RC"
    fi
  done
  echo -e "  ${YELLOW}⚠${NC}  Run: source ~/.bashrc  (or open a new terminal)"
fi

# ── Optional: ffmpeg check ─────────────────────────────────────────────────────

echo ""
if command -v ffmpeg &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} ffmpeg detected (video plugin ready)"
else
  echo -e "  ${YELLOW}⚠${NC}  ffmpeg not found — video plugin disabled"
  echo -e "       Install: sudo apt install ffmpeg"
fi

# ── Done ───────────────────────────────────────────────────────────────────────

echo ""
echo -e "  ${GREEN}✅ Buddy is ready!${NC}"
echo ""
echo -e "  Type  ${CYAN}buddy${NC}          → open full TUI"
echo -e "  Type  ${CYAN}buddy \"tasks\"${NC}  → quick one-shot command"
echo -e "  Type  ${CYAN}buddy \"help\"${NC}   → see all commands"
echo ""
