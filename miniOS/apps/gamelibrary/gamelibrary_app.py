#!/usr/bin/env python3
"""
MiniOS Game Library
Scans locally installed game launchers (Steam, Lutris) for owned/installed
games and shows them as a clickable icon grid — like Playnite. No login
automation: Steam/Lutris/Xbox App handle their own sign-in in their own
windows; this just reads what's already installed and launches it.

Requires: python3-gi, gir1.2-gtk-3.0, python3-vdf (for Steam library parsing)
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio
import os
import glob
import subprocess
import re

STEAM_ROOT = os.path.expanduser("~/.steam/steam")
STEAM_LIBRARY_VDF = os.path.join(STEAM_ROOT, "steamapps", "libraryfolders.vdf")
LUTRIS_GAMES_DIR = os.path.expanduser("~/.local/share/lutris/games")


def find_steam_games():
    """Parse Steam's appmanifest_*.acf files across all library folders."""
    games = []
    lib_dirs = [os.path.join(STEAM_ROOT, "steamapps")]

    if os.path.exists(STEAM_LIBRARY_VDF):
        with open(STEAM_LIBRARY_VDF, "r", errors="ignore") as f:
            content = f.read()
        for path in re.findall(r'"path"\s*"([^"]+)"', content):
            lib_dirs.append(os.path.join(path, "steamapps"))

    for lib in lib_dirs:
        for acf in glob.glob(os.path.join(lib, "appmanifest_*.acf")):
            try:
                with open(acf, "r", errors="ignore") as f:
                    content = f.read()
                appid = re.search(r'"appid"\s*"(\d+)"', content)
                name = re.search(r'"name"\s*"([^"]+)"', content)
                if appid and name:
                    games.append({
                        "name": name.group(1),
                        "launch_cmd": ["xdg-open", f"steam://rungameid/{appid.group(1)}"],
                        "source": "Steam",
                    })
            except Exception:
                continue
    return games


def find_lutris_games():
    """List games known to Lutris via its `lutris` CLI, if installed."""
    games = []
    if not shutil_which("lutris"):
        return games
    try:
        out = subprocess.run(["lutris", "-l"], capture_output=True, text=True, timeout=10).stdout
        for line in out.strip().splitlines():
            # Lutris -l format: "id | Name | Runner"
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and parts[0].isdigit():
                games.append({
                    "name": parts[1],
                    "launch_cmd": ["lutris", f"lutris:rungameid/{parts[0]}"],
                    "source": "Lutris",
                })
    except Exception:
        pass
    return games


def shutil_which(cmd):
    from shutil import which
    return which(cmd)


class GameLibrary(Gtk.Window):
    def __init__(self):
        super().__init__(title="MiniOS Game Library")
        self.set_default_size(700, 500)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(15)
        self.add(vbox)

        header = Gtk.Box(spacing=10)
        header.pack_start(Gtk.Label(label="<b>Game Library</b>", use_markup=True), False, False, 0)
        rescan_btn = Gtk.Button(label="Rescan")
        rescan_btn.connect("clicked", lambda b: self.load_games())
        header.pack_end(rescan_btn, False, False, 0)
        vbox.add(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(6)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.flowbox)
        vbox.add(scroll)

        self.status = Gtk.Label(label="", xalign=0)
        vbox.add(self.status)

        self.load_games()

    def load_games(self):
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)

        games = find_steam_games() + find_lutris_games()

        if not games:
            self.status.set_text(
                "No games found. Install Steam or Lutris and add games there "
                "first — this scans what's already installed, it doesn't "
                "install anything itself."
            )
            return

        self.status.set_text(f"{len(games)} game(s) found.")
        for game in games:
            tile = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            icon = Gtk.Image.new_from_icon_name("applications-games", Gtk.IconSize.DIALOG)
            box.pack_start(icon, False, False, 0)
            box.pack_start(Gtk.Label(label=game["name"], wrap=True), False, False, 0)
            box.pack_start(Gtk.Label(label=f"<i>{game['source']}</i>", use_markup=True), False, False, 0)
            tile.add(box)
            tile.connect("clicked", self.launch_game, game)
            self.flowbox.add(tile)
        self.flowbox.show_all()

    def launch_game(self, _btn, game):
        subprocess.Popen(game["launch_cmd"])


if __name__ == "__main__":
    win = GameLibrary()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
