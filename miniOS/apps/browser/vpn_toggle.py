#!/usr/bin/env python3
"""
MiniOS VPN Toggle
A small always-on-top switch that brings a WireGuard tunnel up/down.
BYO provider: drop a .conf file from Mullvad / ProtonVPN / AirVPN / your
own server into ~/.config/miniOS/vpn/, pick it from the dropdown, flip the
switch. This app does not include or connect to any VPN network itself.

Requires: python3-gi, gir1.2-gtk-3.0, wireguard-tools
The launching user needs passwordless sudo for `wg-quick` (set up via a
narrow /etc/sudoers.d rule — see live-build/config/includes.chroot).
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import subprocess
import os
import glob

VPN_DIR = os.path.expanduser("~/.config/miniOS/vpn")


def run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, (result.stdout + result.stderr)
    except Exception as e:
        return False, str(e)


class VpnToggle(Gtk.Window):
    def __init__(self):
        super().__init__(title="VPN")
        self.set_default_size(320, 140)
        self.set_border_width(15)
        self.active_conf = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        vbox.add(Gtk.Label(label="<b>VPN (WireGuard)</b>", use_markup=True, xalign=0))

        os.makedirs(VPN_DIR, exist_ok=True)
        self.combo = Gtk.ComboBoxText()
        self.reload_profiles()
        vbox.add(self.combo)

        hint = Gtk.Label(
            label=f"Drop a .conf from your VPN provider into:\n{VPN_DIR}",
            xalign=0,
        )
        hint.set_line_wrap(True)
        vbox.add(hint)

        row = Gtk.Box(spacing=10)
        self.switch = Gtk.Switch()
        self.switch.connect("state-set", self.on_toggle)
        row.pack_start(Gtk.Label(label="Connected"), False, False, 0)
        row.pack_start(self.switch, False, False, 0)
        vbox.add(row)

        self.status = Gtk.Label(label="Disconnected", xalign=0)
        vbox.add(self.status)

    def reload_profiles(self):
        self.combo.remove_all()
        confs = glob.glob(os.path.join(VPN_DIR, "*.conf"))
        if not confs:
            self.combo.append_text("(no .conf files found)")
        for c in confs:
            self.combo.append_text(os.path.basename(c))
        self.combo.set_active(0)

    def on_toggle(self, switch, state):
        profile = self.combo.get_active_text()
        if not profile or profile.startswith("("):
            self.status.set_text("Add a .conf file first.")
            switch.set_state(False)
            return True

        conf_path = os.path.join(VPN_DIR, profile)
        iface = profile.replace(".conf", "")

        if state:
            ok, out = run(["sudo", "wg-quick", "up", conf_path])
            self.status.set_text("Connected" if ok else f"Failed: {out.strip()[:80]}")
            self.active_conf = conf_path if ok else None
        else:
            target = self.active_conf or conf_path
            ok, out = run(["sudo", "wg-quick", "down", target])
            self.status.set_text("Disconnected" if ok else f"Failed: {out.strip()[:80]}")
            self.active_conf = None

        return False  # allow default state change


if __name__ == "__main__":
    win = VpnToggle()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
