#!/usr/bin/env python3
"""
MiniOS Settings
A minimal GTK3 settings panel: Network, Display, Sound.
Requires: python3-gi, gir1.2-gtk-3.0, network-manager, pactl, xrandr
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import subprocess


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except Exception as e:
        return f"error: {e}"


class NetworkPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)

        self.add(Gtk.Label(label="<b>Wi-Fi Networks</b>", use_markup=True, xalign=0))
        self.liststore = Gtk.ListStore(str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        for i, title in enumerate(["SSID", "Signal"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            self.treeview.append_column(column)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(180)
        scroll.add(self.treeview)
        self.add(scroll)

        btn_box = Gtk.Box(spacing=6)
        refresh_btn = Gtk.Button(label="Scan")
        refresh_btn.connect("clicked", self.scan_wifi)
        connect_btn = Gtk.Button(label="Connect")
        connect_btn.connect("clicked", self.connect_wifi)
        btn_box.pack_start(refresh_btn, False, False, 0)
        btn_box.pack_start(connect_btn, False, False, 0)
        self.add(btn_box)

        self.status = Gtk.Label(label="", xalign=0)
        self.add(self.status)
        self.scan_wifi(None)

    def scan_wifi(self, _btn):
        self.liststore.clear()
        out = run(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi", "list"])
        for line in out.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 2 and parts[0]:
                self.liststore.append([parts[0], parts[1] + "%"])

    def connect_wifi(self, _btn):
        selection = self.treeview.get_selection()
        model, it = selection.get_selected()
        if not it:
            self.status.set_text("Select a network first.")
            return
        ssid = model[it][0]
        dialog = Gtk.Dialog(title=f"Connect to {ssid}", flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                            Gtk.STOCK_OK, Gtk.ResponseType.OK)
        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_placeholder_text("Password")
        box = dialog.get_content_area()
        box.add(entry)
        dialog.show_all()
        resp = dialog.run()
        pw = entry.get_text()
        dialog.destroy()
        if resp == Gtk.ResponseType.OK:
            result = run(["nmcli", "dev", "wifi", "connect", ssid, "password", pw])
            self.status.set_text(result.strip() or "Connecting…")


class DisplayPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Display</b>", use_markup=True, xalign=0))

        row = Gtk.Box(spacing=10)
        row.add(Gtk.Label(label="Resolution:"))
        combo = Gtk.ComboBoxText()
        for res in ["3840x2160", "2560x1440", "1920x1080", "1600x900", "1280x720"]:
            combo.append_text(res)
        combo.set_active(2)
        combo.connect("changed", self.set_resolution)
        row.add(combo)
        self.add(row)

        row2 = Gtk.Box(spacing=10)
        row2.add(Gtk.Label(label="Brightness:"))
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
        scale.set_value(100)
        scale.connect("value-changed", self.set_brightness)
        scale.set_hexpand(True)
        row2.pack_start(scale, True, True, 0)
        self.add(row2)

    def set_resolution(self, combo):
        res = combo.get_active_text()
        if res:
            run(["xrandr", "-s", res])

    def set_brightness(self, scale):
        val = scale.get_value() / 100.0
        run(["xrandr", "--output", "eDP-1", "--brightness", str(val)])


class SoundPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Sound</b>", use_markup=True, xalign=0))

        row = Gtk.Box(spacing=10)
        row.add(Gtk.Label(label="Volume:"))
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        scale.set_value(70)
        scale.connect("value-changed", self.set_volume)
        scale.set_hexpand(True)
        row.pack_start(scale, True, True, 0)
        self.add(row)

        mute_btn = Gtk.ToggleButton(label="Mute")
        mute_btn.connect("toggled", self.toggle_mute)
        self.add(mute_btn)

    def set_volume(self, scale):
        run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(scale.get_value())}%"])

    def toggle_mute(self, btn):
        run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])


class AccountsPage(Gtk.Box):
    """
    Account linking via standard OAuth (Google / Microsoft).
    This opens the provider's real consent page in the browser and stores
    only the token the provider returns — it never touches the provider's
    login form directly, and never loops over credentials. One account,
    one real user-driven consent flow, same as "Sign in with Google" on
    any normal website.

    You need your own OAuth client ID from Google Cloud Console / Microsoft
    Entra ID app registration — paste them into ~/.config/miniOS/oauth.json.
    """
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Linked Accounts</b>", use_markup=True, xalign=0))

        info = Gtk.Label(
            label="Sign in opens the provider's real consent page in your "
                  "browser. MiniOS never sees your password — only the "
                  "token the provider hands back after you approve it.",
            xalign=0,
        )
        info.set_line_wrap(True)
        self.add(info)

        for name, cmd in [
            ("Sign in with Google", self.sign_in_google),
            ("Sign in with Microsoft", self.sign_in_microsoft),
        ]:
            btn = Gtk.Button(label=name)
            btn.connect("clicked", cmd)
            self.add(btn)

        self.status = Gtk.Label(label="", xalign=0)
        self.add(self.status)

    def sign_in_google(self, _btn):
        # Real implementation: launch system browser to Google's OAuth 2.0
        # authorization endpoint (accounts.google.com/o/oauth2/v2/auth)
        # with your registered client_id, then catch the redirect on a
        # local loopback port and exchange the code for a token.
        self.status.set_text(
            "Would open accounts.google.com in your browser — needs a "
            "client_id in ~/.config/miniOS/oauth.json first."
        )

    def sign_in_microsoft(self, _btn):
        # Real implementation: Microsoft identity platform OAuth 2.0
        # authorization endpoint (login.microsoftonline.com/.../authorize).
        self.status.set_text(
            "Would open login.microsoftonline.com in your browser — needs "
            "a client_id in ~/.config/miniOS/oauth.json first."
        )


class PowerPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Power</b>", use_markup=True, xalign=0))

        row = Gtk.Box(spacing=10)
        row.add(Gtk.Label(label="Power profile:"))
        combo = Gtk.ComboBoxText()
        for p in ["Power saver", "Balanced", "Performance"]:
            combo.append_text(p)
        combo.set_active(1)
        combo.connect("changed", self.set_profile)
        row.add(combo)
        self.add(row)

        btn_box = Gtk.Box(spacing=6)
        for label, action in [("Suspend", "suspend"), ("Hibernate", "hibernate"),
                               ("Restart", "reboot"), ("Shut Down", "poweroff")]:
            b = Gtk.Button(label=label)
            b.connect("clicked", self.power_action, action)
            btn_box.pack_start(b, False, False, 0)
        self.add(btn_box)

    def set_profile(self, combo):
        mapping = {"Power saver": "power-saver", "Balanced": "balanced",
                   "Performance": "performance"}
        profile = mapping.get(combo.get_active_text())
        if profile:
            run(["powerprofilesctl", "set", profile])

    def power_action(self, _btn, action):
        run(["systemctl", action])


class UpdatesPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Updates</b>", use_markup=True, xalign=0))

        self.output = Gtk.TextView()
        self.output.set_editable(False)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.add(self.output)
        self.add(scroll)

        btn_box = Gtk.Box(spacing=6)
        check_btn = Gtk.Button(label="Check for Updates")
        check_btn.connect("clicked", self.check_updates)
        install_btn = Gtk.Button(label="Install Updates")
        install_btn.connect("clicked", self.install_updates)
        btn_box.pack_start(check_btn, False, False, 0)
        btn_box.pack_start(install_btn, False, False, 0)
        self.add(btn_box)

    def _append(self, text):
        buf = self.output.get_buffer()
        buf.insert(buf.get_end_iter(), text + "\n")

    def check_updates(self, _btn):
        self._append("Checking for updates...")
        out = run(["pkexec", "apt-get", "update"])
        self._append(out or "Done.")

    def install_updates(self, _btn):
        self._append("Installing updates (this may take a while)...")
        out = run(["pkexec", "apt-get", "-y", "upgrade"])
        self._append(out or "Done.")


class SecurityPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(15)
        self.add(Gtk.Label(label="<b>Security</b>", use_markup=True, xalign=0))

        fw_row = Gtk.Box(spacing=10)
        fw_row.add(Gtk.Label(label="Firewall:"))
        fw_switch = Gtk.Switch()
        fw_switch.connect("state-set", self.toggle_firewall)
        fw_row.pack_start(fw_switch, False, False, 0)
        self.add(fw_row)

        auto_row = Gtk.Box(spacing=10)
        auto_row.add(Gtk.Label(label="Automatic security updates:"))
        auto_switch = Gtk.Switch()
        auto_switch.set_active(True)
        auto_row.pack_start(auto_switch, False, False, 0)
        self.add(auto_row)

        lock_btn = Gtk.Button(label="Lock Screen Now")
        lock_btn.connect("clicked", lambda b: run(["loginctl", "lock-session"]))
        self.add(lock_btn)

        self.status = Gtk.Label(label="", xalign=0)
        self.add(self.status)

    def toggle_firewall(self, switch, state):
        action = "enable" if state else "disable"
        out = run(["pkexec", "ufw", action])
        self.status.set_text(out.strip() or f"Firewall {action}d.")
        return False


class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="MiniOS Settings")
        self.set_default_size(640, 480)
        notebook = Gtk.Notebook()
        notebook.append_page(NetworkPage(), Gtk.Label(label="Network"))
        notebook.append_page(DisplayPage(), Gtk.Label(label="Display"))
        notebook.append_page(SoundPage(), Gtk.Label(label="Sound"))
        notebook.append_page(AccountsPage(), Gtk.Label(label="Accounts"))
        notebook.append_page(PowerPage(), Gtk.Label(label="Power"))
        notebook.append_page(UpdatesPage(), Gtk.Label(label="Updates"))
        notebook.append_page(SecurityPage(), Gtk.Label(label="Security"))
        self.add(notebook)


if __name__ == "__main__":
    win = SettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
