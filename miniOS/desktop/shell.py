#!/usr/bin/env python3
"""
MiniOS Shell
The desktop is a bottom launcher bar (Settings, Browser, Task Manager,
Games, Terminal, Install) plus a top taskbar. No taskbar clutter beyond
that, no start menu. Runs as the Openbox autostart app.
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, Gdk, GLib, Wnck
import subprocess
from datetime import datetime

APPS_DIR = "/usr/local/bin"  # where the .py apps get installed on the ISO

APPS = [
    ("Settings", "preferences-system", f"{APPS_DIR}/minios-settings"),
    ("Browser", "web-browser", f"{APPS_DIR}/minios-browser"),
    ("Task Manager", "utilities-system-monitor", f"{APPS_DIR}/minios-taskmanager"),
    ("Games", "applications-games", f"{APPS_DIR}/minios-gamelibrary"),
    ("Terminal", "utilities-terminal", f"{APPS_DIR}/minios-admin-terminal"),
    ("Install MiniOS", "drive-harddisk", ["pkexec", "calamares"]),
]


class Taskbar(Gtk.Window):
    """Slim top bar: running windows on the left, clock on the right."""
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.stick()

        screen = Gdk.Screen.get_default()
        self.set_default_size(screen.get_width(), 30)
        self.move(0, 0)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_border_width(4)
        self.add(bar)

        self.windows_box = Gtk.Box(spacing=6)
        bar.pack_start(self.windows_box, True, True, 0)

        self.clock_label = Gtk.Label()
        bar.pack_end(self.clock_label, False, False, 8)

        self.wnck_screen = Wnck.Screen.get_default()
        self.wnck_screen.connect("window-opened", lambda s, w: self.refresh_windows())
        self.wnck_screen.connect("window-closed", lambda s, w: self.refresh_windows())
        self.refresh_windows()

        self.update_clock()
        GLib.timeout_add_seconds(1, self.update_clock)

    def refresh_windows(self):
        for child in self.windows_box.get_children():
            self.windows_box.remove(child)
        for w in self.wnck_screen.get_windows():
            if w.is_skip_taskbar():
                continue
            btn = Gtk.Button(label=w.get_name()[:24])
            btn.connect("clicked", lambda b, win=w: win.activate(0))
            self.windows_box.pack_start(btn, False, False, 0)
        self.windows_box.show_all()

    def update_clock(self):
        self.clock_label.set_text(datetime.now().strftime("%a %H:%M"))
        return True


class Shell(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.stick()

        screen = Gdk.Screen.get_default()
        width = screen.get_width()
        self.set_default_size(width, 70)
        self.move(0, screen.get_height() - 70)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        bar.set_halign(Gtk.Align.CENTER)
        bar.set_valign(Gtk.Align.CENTER)
        self.add(bar)

        for label, icon_name, cmd in APPS:
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
            box.pack_start(img, False, False, 0)
            box.pack_start(Gtk.Label(label=label), False, False, 0)
            btn.add(box)
            btn.connect("clicked", self.launch, cmd)
            bar.pack_start(btn, False, False, 0)

    def launch(self, _btn, cmd):
        subprocess.Popen(cmd if isinstance(cmd, list) else [cmd])


if __name__ == "__main__":
    taskbar = Taskbar()
    taskbar.show_all()

    win = Shell()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
