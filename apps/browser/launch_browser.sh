#!/bin/bash
# MiniOS Browser launcher
# Opens Firefox (privacy-hardened profile) and the VPN toggle side panel.

BROWSER_PROFILE_DIR="$HOME/.config/miniOS/firefox-profile"
mkdir -p "$BROWSER_PROFILE_DIR"

# Launch VPN toggle window (non-blocking, small window pinned top-right by WM rule)
python3 "$(dirname "$0")/vpn_toggle.py" &

# Launch Firefox with its own profile so it doesn't touch the user's real one
exec firefox --profile "$BROWSER_PROFILE_DIR" --no-remote
