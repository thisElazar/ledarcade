#!/bin/bash
# provision.sh — Full setup for a new Wonder Cabinet.
#
# Run on a fresh Raspberry Pi OS Lite (64-bit) after setting hostname,
# SSH, and WiFi via Raspberry Pi Imager.
#
# Usage:
#   scp provision.sh user@wondercabinet001.local:~
#   ssh user@wondercabinet001.local
#   sudo bash provision.sh
#
# What it does:
#   1. Installs system packages
#   2. Disables onboard audio (conflicts with LED matrix timing)
#   3. Builds the rpi-rgb-led-matrix library + Python bindings
#   4. Clones the LED Arcade repo from the stable branch
#   5. Writes cabinet_config.json with standard HUB75 wiring
#   6. Installs systemd services
#   7. Reboots
#
# Prerequisites:
#   - Raspberry Pi OS Lite (64-bit) flashed via Imager
#   - Hostname set (e.g. wondercabinet001) — used as cabinet_id
#   - SSH enabled
#   - Internet access (Ethernet or WiFi)

set -e

# --- Who are we? ---
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
REAL_HOME=$(eval echo "~$REAL_USER")
HOSTNAME=$(hostname)

echo "========================================"
echo " Wonder Cabinet Provisioning"
echo "========================================"
echo " Host:  $HOSTNAME"
echo " User:  $REAL_USER"
echo " Home:  $REAL_HOME"
echo "========================================"
echo ""

# --- System packages ---
echo "[1/6] Installing system packages..."
apt update && apt upgrade -y
apt install -y git python3-pip python3-dev python3-numpy python3-pil cython3

# --- Disable onboard audio ---
echo "[2/6] Disabling onboard audio..."
sed -i 's/^dtparam=audio=on/dtparam=audio=off/' /boot/firmware/config.txt 2>/dev/null || true
echo 'blacklist snd_bcm2835' > /etc/modprobe.d/blacklist-sound.conf

# --- Build LED matrix library ---
echo "[3/6] Building LED matrix library..."
LIB_DIR="$REAL_HOME/rpi-rgb-led-matrix"
if [ ! -d "$LIB_DIR" ]; then
    sudo -u "$REAL_USER" git clone https://github.com/hzeller/rpi-rgb-led-matrix.git "$LIB_DIR"
fi
cd "$LIB_DIR"
make -j$(nproc)
pip install . --break-system-packages

# --- Clone LED Arcade ---
echo "[4/6] Cloning LED Arcade..."
REPO_DIR="$REAL_HOME/led-arcade"
if [ ! -d "$REPO_DIR" ]; then
    sudo -u "$REAL_USER" git clone -b stable https://github.com/thisElazar/ledarcade.git "$REPO_DIR"
fi

# --- Write cabinet config ---
echo "[5/6] Writing cabinet config..."
cat > "$REPO_DIR/cabinet_config.json" <<EOF
{
  "cabinet_id": "$HOSTNAME",
  "hardware_mapping": "regular",
  "gpio_slowdown": 2,
  "button_pins": {
    "up": 5,
    "down": 6,
    "left": 12,
    "right": 13,
    "action_l": 16,
    "action_r": 26
  }
}
EOF
chown "$REAL_USER:$REAL_USER" "$REPO_DIR/cabinet_config.json"

# --- Install services ---
echo "[6/6] Installing services..."
cd "$REPO_DIR"
bash setup.sh

echo ""
echo "========================================"
echo " Done! Rebooting in 5 seconds..."
echo " Cabinet ID: $HOSTNAME"
echo "========================================"
sleep 5
reboot
