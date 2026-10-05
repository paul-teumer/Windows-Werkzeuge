"""Gemeinsame Farbschemata und Oberflächenelemente."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

FONT_FAMILY = "Segoe UI"

LIGHT = {
    "background": "#f3f4f7",
    "surface": "#ffffff",
    "sidebar": "#e9ebf0",
    "border": "#dcdfe6",
    "text": "#1b1f29",
    "muted": "#687083",
    "accent": "#2f6fed",
    "accent_hover": "#2559c4",
    "accent_text": "#ffffff",
    "hover": "#dde1ea",
    "track": "#c5cad6",
    "success": "#17874a",
    "warning": "#b86e00",
    "danger": "#c93a45",
}

DARK = {
    "background": "#14161b",
    "surface": "#1d2027",
    "sidebar": "#101216",
    "border": "#2d313b",
    "text": "#e9ebf0",
    "muted": "#8f97a8",
    "accent": "#5b93ff",
    "accent_hover": "#7aa8ff",
    "accent_text": "#0a1020",
    "hover": "#262a33",
    "track": "#3a3f4b",
    "success": "#4cc38a",
    "warning": "#e5a03c",
    "danger": "#ef6b74",
}


def system_prefers_dark() -> bool:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        ) as key:
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except OSError:
        return False


def font(size: int = 10, weight: str = "normal") -> tuple[str, int, str]:
    return (FONT_FAMILY, size, weight)


def pixels(master: tk.Misc, value: float) -> int:
    """Rechnet eine Größe bei 96 dpi in Bildschirmpixel um."""
    return round(value * master.winfo_fpixels("1i") / 96)


def _rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


_image_cache: dict[tuple, tk.PhotoImage] = {}


def shape_image(master: tk.Misc, width: int, height: int, background: str, shapes: tuple) -> tk.PhotoImage:
    """Kantengeglättetes Bild aus abgerundeten Rechtecken (left, top, right, bottom, radius, color)."""
    key = (width, height, background, shapes)
    if key in _image_cache:
        return _image_cache[key]
    base = _rgb(background)
    rows = []
    for row in range(height):
        cells = []
        for column in range(width):
            red, green, blue = base
            x, y = column + 0.5, row + 0.5
            for left, top, right, bottom, radius, color in shapes:
                qx = abs(x - (left + right) / 2) - ((right - left) / 2 - radius)
                qy = abs(y - (top + bottom) / 2) - ((bottom - top) / 2 - radius)
                distance = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius
                coverage = max(0.0, min(1.0, 0.5 - distance))
                if coverage > 0:
                    target = _rgb(color)
                    red += (target[0] - red) * coverage
                    green += (target[1] - green) * coverage
                    blue += (target[2] - blue) * coverage
            cells.append(f"#{round(red):02x}{round(green):02x}{round(blue):02x}")
        rows.append("{" + " ".join(cells) + "}")
    image = tk.PhotoImage(master=master, width=width, height=height)
    image.put(" ".join(rows))
    _image_cache[key] = image
    return image


def configure_styles(root: tk.Misc, palette: dict[str, str]) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=palette["surface"], foreground=palette["text"], font=font())
    style.configure("TFrame", background=palette["surface"])
    style.configure("TLabel", background=palette["surface"], foreground=palette["text"])

    for name in ("TSpinbox", "TCombobox", "TEntry"):
        style.configure(
            name,
            fieldbackground=palette["background"],
            background=palette["background"],
            foreground=palette["text"],
            arrowcolor=palette["muted"],
            bordercolor=palette["border"],
            lightcolor=palette["border"],
            darkcolor=palette["border"],
            insertcolor=palette["text"],
            padding=5,
            arrowsize=pixels(root, 18),
        )
        style.map(
            name,
            bordercolor=[("focus", palette["accent"])],
            lightcolor=[("focus", palette["accent"])],
            darkcolor=[("focus", palette["accent"])],
            fieldbackground=[("readonly", palette["background"])],
            foreground=[("readonly", palette["text"])],
            selectbackground=[("readonly", palette["background"])],
            selectforeground=[("readonly", palette["text"])],
        )
    root.option_add("*TCombobox*Listbox.background", palette["surface"])
    root.option_add("*TCombobox*Listbox.foreground", palette["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", palette["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", palette["accent_text"])

    style.configure(
        "Horizontal.TScale",
        background=palette["surface"],
        troughcolor=palette["track"],
        bordercolor=palette["surface"],
        lightcolor=palette["accent"],
        darkcolor=palette["accent"],
    )
    style.configure(
        "Treeview",
        background=palette["surface"],
        fieldbackground=palette["surface"],
        foreground=palette["text"],
        bordercolor=palette["border"],
        lightcolor=palette["surface"],
        darkcolor=palette["surface"],
        rowheight=30,
        font=font(),
    )
    style.map("Treeview", background=[("selected", palette["hover"])], foreground=[("selected", palette["text"])])
    style.configure(
        "Treeview.Heading",
        background=palette["surface"],
        foreground=palette["muted"],
        bordercolor=palette["border"],
        lightcolor=palette["surface"],
        darkcolor=palette["surface"],
        relief="flat",
        font=font(9, "bold"),
        padding=(8, 6),
    )
    style.map("Treeview.Heading", background=[("active", palette["surface"])])
    style.configure(
        "Vertical.TScrollbar",
        background=palette["track"],
        troughcolor=palette["surface"],
        bordercolor=palette["surface"],
        arrowcolor=palette["muted"],
        lightcolor=palette["track"],
        darkcolor=palette["track"],
    )
    style.configure(
        "TProgressbar",
        background=palette["accent"],
        troughcolor=palette["track"],
        bordercolor=palette["surface"],
        lightcolor=palette["accent"],
        darkcolor=palette["accent"],
    )


class Button(tk.Canvas):
    """Abgerundete Schaltfläche mit Hover-Zustand."""

    def __init__(self, master, palette, text, command, primary=False, danger=False, backdrop=None):
        self.palette = palette
        self.backdrop = backdrop or palette["surface"]
        self.command = command
        self.primary = primary
        self.danger = danger
        self.enabled = True
        self.text = text
        self.typeface = tkfont.Font(root=master, family=FONT_FAMILY, size=10, weight="bold" if primary else "normal")
        self.button_width = self.typeface.measure(text) + 2 * pixels(master, 20)
        self.button_height = pixels(master, 38)
        super().__init__(
            master, width=self.button_width, height=self.button_height, highlightthickness=0,
            background=self.backdrop, cursor="hand2",
        )
        self.bind("<Enter>", lambda event: self._paint(hover=True))
        self.bind("<Leave>", lambda event: self._paint(hover=False))
        self.bind("<Button-1>", self._click)
        self._paint(hover=False)

    def _colors(self, hover: bool) -> tuple[str, str]:
        palette = self.palette
        if not self.enabled:
            return palette["hover"], palette["muted"]
        if self.primary:
            return (palette["accent_hover"] if hover else palette["accent"]), palette["accent_text"]
        if self.danger:
            return (palette["danger"], palette["accent_text"]) if hover else (palette["hover"], palette["danger"])
        return (palette["track"] if hover else palette["hover"]), palette["text"]

    def _paint(self, hover: bool) -> None:
        fill, foreground = self._colors(hover)
        width, height = self.button_width, self.button_height
        radius = pixels(self, 8)
        self.image = shape_image(self, width, height, self.backdrop, ((0, 0, width, height, radius, fill),))
        self.delete("all")
        self.create_image(0, 0, image=self.image, anchor="nw")
        self.create_text(width / 2, height / 2, text=self.text, font=self.typeface, fill=foreground)
        self.configure(cursor="hand2" if self.enabled else "arrow")

    def _click(self, event) -> None:
        if self.enabled:
            self.command()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._paint(hover=False)


class Switch(tk.Canvas):
    """Ein-/Aus-Schalter, gekoppelt an eine BooleanVar."""

    def __init__(self, master, palette, variable: tk.BooleanVar, command=None):
        self.switch_width, self.switch_height = pixels(master, 44), pixels(master, 24)
        super().__init__(
            master, width=self.switch_width, height=self.switch_height, highlightthickness=0,
            background=palette["surface"], cursor="hand2",
        )
        self.palette = palette
        self.variable = variable
        self.command = command
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *arguments: self._paint())
        self._paint()

    def _toggle(self, event) -> None:
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _paint(self) -> None:
        width, height = self.switch_width, self.switch_height
        on = self.variable.get()
        inset = pixels(self, 3)
        diameter = height - 2 * inset
        knob_left = width - inset - diameter if on else inset
        track = self.palette["accent"] if on else self.palette["track"]
        self.image = shape_image(
            self, width, height, self.palette["surface"],
            ((0, 0, width, height, height / 2, track), (knob_left, inset, knob_left + diameter, inset + diameter, diameter / 2, "#ffffff")),
        )
        self.delete("all")
        self.create_image(0, 0, image=self.image, anchor="nw")


class Card(tk.Frame):
    """Abgesetzter Bereich mit Titel und Erläuterung."""

    def __init__(self, master, palette, title: str, description: str = ""):
        super().__init__(master, background=palette["surface"], highlightbackground=palette["border"], highlightthickness=1)
        self.palette = palette
        header = tk.Frame(self, background=palette["surface"])
        header.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(header, text=title, font=font(11, "bold"), background=palette["surface"], foreground=palette["text"]).pack(anchor="w")
        if description:
            explanation = tk.Label(
                header, text=description, font=font(9), background=palette["surface"], foreground=palette["muted"],
                justify="left", wraplength=300,
            )
            explanation.pack(anchor="w", pady=(2, 0))
            header.bind("<Configure>", lambda event: explanation.configure(wraplength=max(event.width - 4, 100)))
        self.body = tk.Frame(self, background=palette["surface"])
        self.body.pack(fill="both", expand=True, padx=20, pady=(12, 16))


def label(master, palette, text, muted=False, size=10, weight="normal", **options) -> tk.Label:
    return tk.Label(
        master, text=text, font=font(size, weight), background=palette["surface"],
        foreground=palette["muted"] if muted else palette["text"], **options,
    )
