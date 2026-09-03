#!/usr/bin/env python3
"""
MiniOS Task Manager
Live process list with CPU/RAM usage and kill button.
Requires: python3-gi, gir1.2-gtk-3.0, python3-psutil
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import psutil
import signal


class TaskManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="MiniOS Task Manager")
        self.set_default_size(700, 450)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(10)
        self.add(vbox)

        # Summary bar
        self.summary = Gtk.Label(xalign=0)
        vbox.pack_start(self.summary, False, False, 0)

        # Process table: PID, Name, User, CPU%, MEM%, Status
        self.store = Gtk.ListStore(int, str, str, float, float, str)
        self.treeview = Gtk.TreeView(model=self.store)

        columns = ["PID", "Name", "User", "CPU %", "MEM %", "Status"]
        for i, title in enumerate(columns):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, renderer, text=i)
            col.set_sort_column_id(i)
            col.set_resizable(True)
            self.treeview.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.add(self.treeview)
        vbox.pack_start(scroll, True, True, 0)

        btn_box = Gtk.Box(spacing=6)
        end_task_btn = Gtk.Button(label="End Task")
        end_task_btn.connect("clicked", self.end_task)
        btn_box.pack_start(end_task_btn, False, False, 0)
        vbox.pack_start(btn_box, False, False, 0)

        self.refresh()
        GLib.timeout_add_seconds(2, self.refresh)

    def refresh(self):
        self.store.clear()
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        self.summary.set_text(
            f"CPU: {cpu:.1f}%   RAM: {mem.percent:.1f}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)"
        )
        procs = []
        for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
            try:
                info = p.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
        for info in procs[:200]:
            self.store.append([
                info["pid"],
                info["name"] or "",
                info["username"] or "",
                round(info["cpu_percent"] or 0, 1),
                round(info["memory_percent"] or 0, 1),
                info["status"] or "",
            ])
        return True  # keep timeout running

    def end_task(self, _btn):
        selection = self.treeview.get_selection()
        model, it = selection.get_selected()
        if not it:
            return
        pid = model[it][0]
        try:
            psutil.Process(pid).send_signal(signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            dialog = Gtk.MessageDialog(
                transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Could not end task: {e}"
            )
            dialog.run()
            dialog.destroy()


if __name__ == "__main__":
    win = TaskManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
