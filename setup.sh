#!/bin/bash
# setup.sh — One-time setup for an LED Arcade cabinet.
# Installs systemd services, compiles boot splash, enables auto-start.
#
# Usage:  sudo bash setup.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "LED Arcade Setup"
echo "================"
echo "Repo: $REPO_DIR"
echo ""

# --- Install systemd services ---

# Install the unit from the repo (single source of truth — carries the
# StartLimit* crash-loop guard), substituting this cabinet's repo path.
sed "s#/home/thiselazar/led-arcade#$REPO_DIR#g" "$REPO_DIR/led-arcade.service" \
    > /etc/systemd/system/led-arcade.service

echo "Installed led-arcade.service"

cat > /etc/systemd/system/led-arcade-splash.service <<EOF
[Unit]
Description=LED Arcade Boot Splash
DefaultDependencies=no
After=local-fs.target
Before=led-arcade.service

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/boot_splash
Restart=no

[Install]
WantedBy=sysinit.target
EOF

echo "Installed led-arcade-splash.service"

# --- Compile boot splash if library is available ---

# Check common locations for the LED matrix library
LIB_DIR=""
for candidate in "$HOME/rpi-rgb-led-matrix" "/home/$(logname 2>/dev/null)/rpi-rgb-led-matrix" "/usr/local"; do
    if [ -f "$candidate/include/led-matrix-c.h" ]; then
        LIB_DIR="$candidate"
        break
    fi
done

if [ -n "$LIB_DIR" ]; then
    echo "Compiling boot_splash (library: $LIB_DIR)..."
    gcc -O2 -o "$REPO_DIR/boot_splash" "$REPO_DIR/boot_splash.c" \
        -I"$LIB_DIR/include" -L"$LIB_DIR/lib" \
        -lrgbmatrix -lstdc++ -lm -lpthread
    echo "boot_splash compiled."
else
    echo "WARNING: rpi-rgb-led-matrix not found, skipping boot_splash compilation."
    echo "         Build it manually after installing the library."
fi

# --- Enable services ---

systemctl daemon-reload
systemctl enable led-arcade.service
systemctl enable led-arcade-splash.service

echo ""
echo "Done. Reboot to start the arcade."
