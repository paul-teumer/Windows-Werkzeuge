"""Tausch der primären und sekundären Maustaste."""

from __future__ import annotations

import argparse
import ctypes
import sys
import tkinter as tk

from .design import DARK, LIGHT, Card, Switch, configure_styles, font, label, system_prefers_dark

SM_SWAPBUTTON = 23
SPI_SETMOUSEBUTTONSWAP = 0x0021
SPIF_UPDATEINIFILE_AND_SENDCHANGE = 0x03


def is_swapped() -> bool:
    return bool(ctypes.windll.user32.GetSystemMetrics(SM_SWAPBUTTON))


def set_swapped(swapped: bool) -> None:
    """Wirkt sofort und bleibt über die Abmeldung hinaus erhalten."""
    ok = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETMOUSEBUTTONSWAP, int(swapped), None, SPIF_UPDATEINIFILE_AND_SENDCHANGE
    )
    if not ok:
        raise OSError("Die Maustasten konnten nicht umgestellt werden.")


def describe(swapped: bool) -> str:
    return "Rechts" if swapped else "Links"


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
        self.geometry("480x340")
        self.resizable(False, False)
        self.configure(background=palette["background"], padx=24, pady=24)
        configure_styles(self, palette)

        tk.Label(self, text="Maustasten", font=font(20, "bold"), background=palette["background"], foreground=palette["text"]).pack(anchor="w")
        tk.Label(self, text="Vertauscht die primäre und die sekundäre Maustaste.", font=font(10), background=palette["background"], foreground=palette["muted"]).pack(anchor="w", pady=(0, 14))

        card = Card(self, palette, "Primäre Taste")
        card.pack(fill="x")
        self.state_label = label(card.body, palette, "", size=16, weight="bold")
        self.state_label.pack(anchor="w")
        row = tk.Frame(card.body, background=palette["surface"])
        row.pack(fill="x", pady=(14, 0))
        self.swapped = tk.BooleanVar(value=is_swapped())
        Switch(row, palette, self.swapped, command=self.apply).pack(side="left")
        label(row, palette, "Tasten vertauschen (für Linkshänder)").pack(side="left", padx=(12, 0))
        self.refresh()

    def refresh(self) -> None:
        self.state_label.configure(text="Rechte Maustaste" if self.swapped.get() else "Linke Maustaste")

    def apply(self) -> None:
        try:
            set_swapped(self.swapped.get())
        except OSError:
            self.swapped.set(is_swapped())
        self.refresh()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maustasten vertauschen.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--wechseln", action="store_true", help="Zustand umschalten, ohne Fenster (z. B. für Tastenkürzel)")
    group.add_argument("--links", action="store_true", help="Linke Taste als primäre Taste")
    group.add_argument("--rechts", action="store_true", help="Rechte Taste als primäre Taste")
    group.add_argument("--status", action="store_true", help="Aktuellen Zustand ausgeben")
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
    else:
        Window().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
