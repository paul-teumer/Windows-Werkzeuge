"""Anzeige der Größe aller Dateien und Unterordner eines Ordners."""

from __future__ import annotations

import csv
import ctypes
import os
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .design import DARK, LIGHT, Button, Card, configure_styles, darken_title_bar, font, label, system_prefers_dark

UNITS = ("B", "KB", "MB", "GB", "TB")
BAR_LENGTH = 14


@dataclass
class Entry:
    name: str
    is_directory: bool
    size: int


def format_size(size: float) -> str:
    value = float(size)
    for unit in UNITS:
        if value < 1024 or unit == UNITS[-1]:
            text = f"{value:.0f}" if unit == "B" else f"{value:.1f}".replace(".", ",")
            return f"{text} {unit}"
        value /= 1024
    return ""


def _is_link(entry: os.DirEntry) -> bool:
    return entry.is_symlink() or (hasattr(entry, "is_junction") and entry.is_junction())


def directory_size(path: str, cancelled: threading.Event | None = None) -> int:
    """Summe aller Dateigrößen unterhalb von `path`; Verknüpfungen werden nicht verfolgt."""
    total = 0
    pending = [path]
    while pending:
        if cancelled is not None and cancelled.is_set():
            return total
        try:
            with os.scandir(pending.pop()) as iterator:
                for entry in iterator:
                    try:
                        if _is_link(entry):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def scan(folder: str, cancelled: threading.Event | None = None):
    """Liefert die Einträge des Ordners nacheinander, sobald deren Größe feststeht."""
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return
    for entry in entries:
        if cancelled is not None and cancelled.is_set():
            return
        try:
            if _is_link(entry):
                continue
            if entry.is_dir(follow_symlinks=False):
                yield Entry(entry.name, True, directory_size(entry.path, cancelled))
            elif entry.is_file(follow_symlinks=False):
                yield Entry(entry.name, False, entry.stat(follow_symlinks=False).st_size)
        except OSError:
            continue


def share_bar(share: float) -> str:
    return "█" * round(share * BAR_LENGTH)


class Application(tk.Tk):
    def __init__(self, folder: str | None = None) -> None:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
        super().__init__()
        self.palette = DARK if system_prefers_dark() else LIGHT
        palette = self.palette
        self.title("Ordnergrößen")
        self.geometry("920x640")
        self.minsize(720, 480)
        self.configure(background=palette["background"], padx=24, pady=22)
        configure_styles(self, palette)
        if palette is DARK:
            darken_title_bar(self)

        self.folder = Path(folder or Path.home()).resolve()
        self.entries: list[Entry] = []
        self.messages: queue.Queue = queue.Queue()
        self.cancelled = threading.Event()
        self.sort_key, self.sort_descending = "size", True

        tk.Label(self, text="Ordnergrößen", font=font(20, "bold"), background=palette["background"], foreground=palette["text"]).pack(anchor="w")
        self.path_label = tk.Label(self, font=font(10), background=palette["background"], foreground=palette["muted"], anchor="w")
        self.path_label.pack(fill="x", pady=(0, 12))

        toolbar = tk.Frame(self, background=palette["background"])
        toolbar.pack(fill="x", pady=(0, 12))
        for text, command, primary in (
            ("Ordner wählen", self.choose_folder, True),
            ("Eine Ebene hoch", self.go_up, False),
            ("Neu einlesen", self.reload, False),
            ("Als CSV speichern", self.export, False),
        ):
            button = Button(toolbar, palette, text, command, primary=primary, backdrop=palette["background"])
            button.pack(side="left", padx=(0, 8))

        card = Card(self, palette, "Inhalt")
        card.pack(fill="both", expand=True)
        columns = ("name", "type", "size", "share")
        self.tree = ttk.Treeview(card.body, columns=columns, show="headings", selectmode="browse")
        for column, heading, width, anchor in (
            ("name", "Name", 340, "w"),
            ("type", "Typ", 80, "w"),
            ("size", "Größe", 100, "e"),
            ("share", "Anteil", 190, "w"),
        ):
            self.tree.heading(column, text=heading, anchor=anchor, command=lambda key=column: self.sort_by(key))
            self.tree.column(column, width=width, anchor=anchor, stretch=column == "name")
        scrollbar = ttk.Scrollbar(card.body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", self.open_selected)
        self.tree.bind("<Return>", self.open_selected)

        self.status = tk.Label(self, font=font(10), background=palette["background"], foreground=palette["muted"], anchor="w")
        self.status.pack(fill="x", pady=(10, 0))
        self.after(80, self.poll)
        self.reload()

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self.folder), title="Ordner wählen")
        if selected:
            self.folder = Path(selected).resolve()
            self.reload()

    def go_up(self) -> None:
        if self.folder.parent != self.folder:
            self.folder = self.folder.parent
            self.reload()

    def open_selected(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        entry = self.entries[int(selection[0])]
        if entry.is_directory:
            self.folder = self.folder / entry.name
            self.reload()

    def reload(self) -> None:
        self.cancelled.set()
        self.cancelled = threading.Event()
        self.entries = []
        self.render()
        self.path_label.configure(text=str(self.folder))
        self.status.configure(text="Wird eingelesen …")
        threading.Thread(target=self.work, args=(str(self.folder), self.cancelled), daemon=True).start()

    def work(self, folder: str, cancelled: threading.Event) -> None:
        for entry in scan(folder, cancelled):
            self.messages.put((cancelled, entry))
        self.messages.put((cancelled, None))

    def poll(self) -> None:
        changed = finished = False
        try:
            while True:
                token, entry = self.messages.get_nowait()
                if token is not self.cancelled:
                    continue
                if entry is None:
                    finished = True
                else:
                    self.entries.append(entry)
                    changed = True
        except queue.Empty:
            pass
        if changed or finished:
            self.render()
        if finished:
            total = sum(entry.size for entry in self.entries)
            self.status.configure(text=f"{len(self.entries)} Einträge · gesamt {format_size(total)}")
        self.after(150, self.poll)

    def sort_by(self, key: str) -> None:
        self.sort_descending = not self.sort_descending if key == self.sort_key else key == "size"
        self.sort_key = key
        self.render()

    def ordered(self) -> list[int]:
        keys = {
            "name": lambda index: self.entries[index].name.lower(),
            "type": lambda index: (not self.entries[index].is_directory, self.entries[index].name.lower()),
            "size": lambda index: self.entries[index].size,
            "share": lambda index: self.entries[index].size,
        }
        return sorted(range(len(self.entries)), key=keys[self.sort_key], reverse=self.sort_descending)

    def render(self) -> None:
        self.tree.delete(*self.tree.get_children())
        total = sum(entry.size for entry in self.entries) or 1
        for index in self.ordered():
            entry = self.entries[index]
            share = entry.size / total
            self.tree.insert(
                "", "end", iid=str(index),
                values=(entry.name + ("/" if entry.is_directory else ""), "Ordner" if entry.is_directory else "Datei",
                        format_size(entry.size), f"{share * 100:5.1f} %  {share_bar(share)}".replace(".", ",")),
            )

    def export(self) -> None:
        target = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV-Datei", "*.csv")], initialfile=f"{self.folder.name or 'Laufwerk'}.csv"
        )
        if not target:
            return
        try:
            with open(target, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(("Name", "Typ", "Größe in Bytes"))
                for index in self.ordered():
                    entry = self.entries[index]
                    writer.writerow((entry.name, "Ordner" if entry.is_directory else "Datei", entry.size))
        except OSError as error:
            messagebox.showerror("Speichern fehlgeschlagen", str(error))


def main() -> None:
    Application().mainloop()
