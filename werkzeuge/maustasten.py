"""Tausch der primären und sekundären Maustaste."""

from __future__ import annotations

import argparse
import ctypes
import sys
import tkinter as tk

from . import hintergrund
from .design import DARK, LIGHT, Button, Card, Switch, configure_styles, darken_title_bar, font, label, system_prefers_dark
from .maus import describe, is_swapped, set_swapped

REFRESH_INTERVAL_MILLISECONDS = 1000


class Window(tk.Tk):
    def __init__(self) -> None:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
        super().__init__()
        palette = DARK if system_prefers_dark() else LIGHT
        self.palette = palette
        self.title("Maustasten")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(background=palette["background"], padx=24, pady=24)
        configure_styles(self, palette)
        if palette is DARK:
            darken_title_bar(self)

        tk.Label(self, text="Maustasten", font=font(20, "bold"), background=palette["background"], foreground=palette["text"]).pack(anchor="w")
        tk.Label(self, text="Vertauscht die primäre und die sekundäre Maustaste.", font=font(10), background=palette["background"], foreground=palette["muted"]).pack(anchor="w", pady=(0, 14))

        card = Card(self, palette, "Primäre Taste", "Gilt für alle angeschlossenen Mäuse gleichzeitig.")
        card.pack(fill="x")
        self.state_label = label(card.body, palette, "", size=16, weight="bold")
        self.state_label.pack(anchor="w")
        row = tk.Frame(card.body, background=palette["surface"])
        row.pack(fill="x", pady=(14, 0))
        self.swapped = tk.BooleanVar(value=is_swapped())
        Switch(row, palette, self.swapped, command=self.apply).pack(side="left")
        label(row, palette, "Tasten vertauschen (für Linkshänder)").pack(side="left", padx=(12, 0))

        quick = Card(
            self, palette, "Schnellzugriff",
            f"Zum raschen Wechseln, etwa wenn eine andere Person die Maus übernimmt. Tastenkürzel: {hintergrund.HOTKEY_TEXT}.",
        )
        quick.pack(fill="x", pady=(14, 0))
        background_row = tk.Frame(quick.body, background=palette["surface"])
        background_row.pack(fill="x")
        self.background = tk.BooleanVar(value=hintergrund.is_running())
        Switch(background_row, palette, self.background, command=self.apply_background).pack(side="left")
        label(background_row, palette, "Im Hintergrund bereitstehen (Autostart)").pack(side="left", padx=(12, 0))
        shortcut_row = tk.Frame(quick.body, background=palette["surface"])
        shortcut_row.pack(fill="x", pady=(14, 0))
        Button(shortcut_row, palette, "Desktop-Verknüpfung anlegen", self.create_shortcut, backdrop=palette["surface"]).pack(side="left")
        self.message = label(quick.body, palette, "", muted=True)
        self.message.pack(anchor="w", pady=(10, 0))

        self.refresh()
        self.after(REFRESH_INTERVAL_MILLISECONDS, self.poll)

    def refresh(self) -> None:
        self.swapped.set(is_swapped())
        self.state_label.configure(text="Rechte Maustaste" if self.swapped.get() else "Linke Maustaste")

    def poll(self) -> None:
        if is_swapped() != self.swapped.get():
            self.refresh()
        self.after(REFRESH_INTERVAL_MILLISECONDS, self.poll)

    def apply(self) -> None:
        try:
            set_swapped(self.swapped.get())
        except OSError:
            pass
        self.refresh()

    def apply_background(self) -> None:
        enabled = self.background.get()
        try:
            hintergrund.set_autostart(enabled)
        except OSError as error:
            self.background.set(not enabled)
            self.message.configure(text=str(error))
            return
        if enabled:
            hintergrund.start()
        else:
            hintergrund.stop()
        self.message.configure(
            text=f"Symbol im Infobereich und {hintergrund.HOTKEY_TEXT} sind aktiv." if enabled else "Hintergrundbetrieb beendet."
        )

    def create_shortcut(self) -> None:
        try:
            path = hintergrund.create_desktop_shortcut()
        except OSError as error:
            self.message.configure(text=str(error))
            return
        self.message.configure(text=f"Angelegt: {path.name} auf dem Desktop.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maustasten vertauschen.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--wechseln", action="store_true", help="Zustand umschalten, ohne Fenster (z. B. für Tastenkürzel)")
    group.add_argument("--links", action="store_true", help="Linke Taste als primäre Taste")
    group.add_argument("--rechts", action="store_true", help="Rechte Taste als primäre Taste")
    group.add_argument("--status", action="store_true", help="Aktuellen Zustand ausgeben")
    group.add_argument("--hintergrund", action="store_true", help=f"Im Infobereich bereitstehen, Tastenkürzel {hintergrund.HOTKEY_TEXT}")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.status:
        print(f"Primäre Maustaste: {describe(is_swapped())}")
    elif arguments.wechseln:
        set_swapped(not is_swapped())
    elif arguments.links:
        set_swapped(False)
    elif arguments.rechts:
        set_swapped(True)
    elif arguments.hintergrund:
        hintergrund.run()
    else:
        Window().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
