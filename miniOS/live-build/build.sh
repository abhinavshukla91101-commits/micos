#!/bin/bash
# Build the MiniOS ISO using Debian live-build.
# Run this on a Debian/Ubuntu machine (or VM) with root, ~20GB free disk,
# and a real internet connection (it downloads the full package set).
#
#   sudo apt install live-build
#   sudo ./build.sh
#
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Run as root: sudo ./build.sh"
  exit 1
fi

cd "$(dirname "$0")"

echo "[1/4] Configuring live-build..."
lb config \
  --distribution bookworm \
  --architecture amd64 \
  --debian-installer live \
  --archive-areas "main contrib non-free non-free-firmware"

echo "[2/4] Copying MiniOS apps into the chroot overlay..."
APP_BIN=config/includes.chroot/usr/local/bin
mkdir -p "$APP_BIN"
cp ../apps/settings/settings_app.py       "$APP_BIN/minios-settings"
cp ../apps/taskmanager/taskmanager_app.py "$APP_BIN/minios-taskmanager"
cp ../apps/browser/launch_browser.sh      "$APP_BIN/minios-browser"
cp ../apps/browser/vpn_toggle.py          "$APP_BIN/minios-vpn-toggle"
cp ../apps/gamelibrary/gamelibrary_app.py "$APP_BIN/minios-gamelibrary"
cp ../apps/terminal/admin_terminal.sh     "$APP_BIN/minios-admin-terminal"
cp ../desktop/shell.py                    "$APP_BIN/minios-shell"
chmod +x "$APP_BIN"/*

echo "[2b/4] Installing boot splash and login screen assets..."
PLYMOUTH_DIR=config/includes.chroot/usr/share/plymouth/themes/minios
mkdir -p "$PLYMOUTH_DIR/spinner"
cp ../desktop/plymouth/minios.plymouth "$PLYMOUTH_DIR/"
cp ../desktop/plymouth/minios.script   "$PLYMOUTH_DIR/"
cp ../desktop/plymouth/logo.png        "$PLYMOUTH_DIR/"
cp ../desktop/plymouth/spinner/*.png   "$PLYMOUTH_DIR/spinner/"

LIGHTDM_DIR=config/includes.chroot/etc/lightdm
BG_DIR=config/includes.chroot/usr/share/backgrounds/minios
mkdir -p "$LIGHTDM_DIR" "$BG_DIR"
cp ../desktop/lightdm/lightdm-gtk-greeter.conf "$LIGHTDM_DIR/"
cp ../desktop/lightdm/login-bg.png    "$BG_DIR/"
cp ../desktop/lightdm/user-default.png "$BG_DIR/"

SKEL=config/includes.chroot/etc/skel
mkdir -p "$SKEL/.config/openbox"
cp ../desktop/openbox/autostart "$SKEL/.config/openbox/autostart"
chmod +x "$SKEL/.config/openbox/autostart"

# (sudoers rule for wg-quick, Plymouth activation, and lightdm setup are
# handled by config/hooks/live/0100-minios-setup.hook.chroot)

echo "[3/4] Building the ISO (this takes a while)..."
lb build

echo "[4/4] Done. Output ISO is in this directory (live-image-amd64.hybrid.iso)."
