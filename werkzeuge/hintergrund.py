"""Hintergrundbetrieb der Maustasten: Tastenkürzel, Symbol im Infobereich, Autostart und Desktop-Verknüpfung."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import winreg
from ctypes import wintypes
from pathlib import Path

from . import maus

WINDOW_CLASS = "MaustastenHintergrund"
MUTEX_NAME = "Local\\MaustastenHintergrund"
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "Maustasten"
SHORTCUT_NAME = "Maustasten tauschen.lnk"
HOTKEY_TEXT = "Strg+Alt+M"

WM_NULL, WM_DESTROY, WM_CLOSE, WM_HOTKEY = 0x0000, 0x0002, 0x0010, 0x0312
WM_LBUTTONUP, WM_RBUTTONUP, WM_TRAY = 0x0202, 0x0205, 0x8001
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, VIRTUAL_KEY_M = 0x0001, 0x0002, 0x4000, 0x4D
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 0x01, 0x02, 0x04, 0x10
NIIF_NOSOUND = 0x10
TPM_RIGHTBUTTON, TPM_RETURNCMD = 0x0002, 0x0100
ERROR_ALREADY_EXISTS = 183
DETACHED_PROCESS, CREATE_NO_WINDOW = 0x00000008, 0x08000000
MENU_TOGGLE, MENU_SETTINGS, MENU_QUIT = 1, 2, 3
ICON_SIZE = 32
SUPERSAMPLING = 4
MOUSE_CENTER, MOUSE_RADIUS, MOUSE_TOP, MOUSE_BOTTOM, BUTTON_BOTTOM = 15.5, 7.5, 3, 29, 14.5

user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WindowProcedure = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WindowClass(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT), ("procedure", WindowProcedure), ("class_extra", ctypes.c_int),
        ("window_extra", ctypes.c_int), ("instance", wintypes.HINSTANCE), ("icon", wintypes.HICON),
        ("cursor", wintypes.HANDLE), ("background", wintypes.HBRUSH), ("menu_name", wintypes.LPCWSTR),
        ("class_name", wintypes.LPCWSTR),
    ]


class Guid(ctypes.Structure):
    _fields_ = [("first", wintypes.DWORD), ("second", wintypes.WORD), ("third", wintypes.WORD), ("rest", ctypes.c_ubyte * 8)]


class NotifyIconData(ctypes.Structure):
    _fields_ = [
        ("size", wintypes.DWORD), ("window", wintypes.HWND), ("identifier", wintypes.UINT),
        ("flags", wintypes.UINT), ("callback_message", wintypes.UINT), ("icon", wintypes.HICON),
        ("tip", wintypes.WCHAR * 128), ("state", wintypes.DWORD), ("state_mask", wintypes.DWORD),
        ("info", wintypes.WCHAR * 256), ("version", wintypes.UINT), ("info_title", wintypes.WCHAR * 64),
        ("info_flags", wintypes.DWORD), ("guid", Guid), ("balloon_icon", wintypes.HICON),
    ]


class Point(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


user32.DefWindowProcW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
user32.DefWindowProcW.restype = LRESULT
user32.CreateWindowExW.argtypes = (
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
)
user32.CreateWindowExW.restype = wintypes.HWND
user32.RegisterClassW.argtypes = (ctypes.POINTER(WindowClass),)
user32.DestroyWindow.argtypes = (wintypes.HWND,)
user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
user32.FindWindowW.restype = wintypes.HWND
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
user32.TranslateMessage.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
user32.CreateIcon.argtypes = (
    wintypes.HINSTANCE, ctypes.c_int, ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_char_p, ctypes.c_char_p,
)
user32.CreateIcon.restype = wintypes.HICON
user32.DestroyIcon.argtypes = (wintypes.HICON,)
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = (wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR)
user32.DestroyMenu.argtypes = (wintypes.HMENU,)
user32.GetCursorPos.argtypes = (ctypes.POINTER(Point),)
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.TrackPopupMenu.argtypes = (
    wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.LPVOID,
)
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
kernel32.CreateMutexW.restype = wintypes.HANDLE
shell32.Shell_NotifyIconW.argtypes = (wintypes.DWORD, ctypes.POINTER(NotifyIconData))


def own_command(*arguments: str) -> list[str]:
    """Befehl, mit dem sich dieses Programm selbst ohne Konsolenfenster erneut starten lässt."""
    if getattr(sys, "frozen", False):
        return [sys.executable, *arguments]
    interpreter = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).resolve().parent.parent / "maustasten_tausch.pyw"
    return [str(interpreter if interpreter.exists() else sys.executable), str(script), *arguments]


def _spawn(*arguments: str) -> None:
    command = own_command(*arguments)
    program_folder = Path(command[0]).parent if getattr(sys, "frozen", False) else Path(command[1]).parent
    subprocess.Popen(
        command, cwd=str(program_folder), env={**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"},
        creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW, close_fds=True,
    )


def is_running() -> bool:
    return bool(user32.FindWindowW(WINDOW_CLASS, None))


def start() -> None:
    if not is_running():
        _spawn("--hintergrund")


def stop() -> None:
    window = user32.FindWindowW(WINDOW_CLASS, None)
    if window:
        user32.PostMessageW(window, WM_CLOSE, 0, 0)


def autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY) as key:
            winreg.QueryValueEx(key, AUTOSTART_NAME)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, subprocess.list2cmdline(own_command("--hintergrund")))
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
            except FileNotFoundError:
                pass


def create_desktop_shortcut() -> Path:
    """Legt auf dem Desktop eine Verknüpfung an, die die Maustasten ohne Fenster umschaltet."""
    command = own_command("--wechseln")
    script = (
        "$link_path = Join-Path ([Environment]::GetFolderPath('Desktop')) $env:LINK_NAME;"
        "$link = (New-Object -ComObject WScript.Shell).CreateShortcut($link_path);"
        "$link.TargetPath = $env:LINK_TARGET; $link.Arguments = $env:LINK_ARGUMENTS;"
        "$link.WorkingDirectory = $env:LINK_DIRECTORY; $link.IconLocation = $env:LINK_ICON;"
        "$link.Description = 'Vertauscht die Maustasten'; $link.Save();"
        "[Console]::OutputEncoding = [Text.Encoding]::UTF8; Write-Output $link_path"
    )
    environment = {
        **os.environ,
        "LINK_NAME": SHORTCUT_NAME,
        "LINK_TARGET": command[0],
        "LINK_ARGUMENTS": subprocess.list2cmdline(command[1:]),
        "LINK_DIRECTORY": str(Path(command[0]).parent),
        "LINK_ICON": f"{command[0]},0",
    }
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment,
        creationflags=CREATE_NO_WINDOW, timeout=30,
    )
    if completed.returncode != 0:
        raise OSError(completed.stderr.strip() or "Die Verknüpfung konnte nicht angelegt werden.")
    return Path(completed.stdout.strip())


def _inside_mouse(x: float, y: float) -> bool:
    if not MOUSE_TOP <= y <= MOUSE_BOTTOM:
        return False
    if y < MOUSE_TOP + MOUSE_RADIUS:
        return (x - MOUSE_CENTER) ** 2 + (y - MOUSE_TOP - MOUSE_RADIUS) ** 2 <= MOUSE_RADIUS**2
    if y > MOUSE_BOTTOM - MOUSE_RADIUS:
        return (x - MOUSE_CENTER) ** 2 + (y - MOUSE_BOTTOM + MOUSE_RADIUS) ** 2 <= MOUSE_RADIUS**2
    return abs(x - MOUSE_CENTER) <= MOUSE_RADIUS


def make_icon(swapped: bool) -> int:
    """Maus-Symbol; die primäre Taste ist hell hervorgehoben."""
    body, highlight, line = (47, 107, 255), (255, 255, 255), (28, 60, 150)
    pixels = bytearray()
    for row in range(ICON_SIZE):
        for column in range(ICON_SIZE):
            red = green = blue = covered = 0
            for sub_row in range(SUPERSAMPLING):
                for sub_column in range(SUPERSAMPLING):
                    x = column + (sub_column + 0.5) / SUPERSAMPLING
                    y = row + (sub_row + 0.5) / SUPERSAMPLING
                    if not _inside_mouse(x, y):
                        continue
                    primary_side = x > MOUSE_CENTER if swapped else x < MOUSE_CENTER
                    on_divider = y < BUTTON_BOTTOM and abs(x - MOUSE_CENTER) < 0.6
                    on_button_edge = abs(y - BUTTON_BOTTOM) < 0.6
                    if on_divider or on_button_edge:
                        color = line
                    elif y < BUTTON_BOTTOM and primary_side:
                        color = highlight
                    else:
                        color = body
                    red, green, blue, covered = red + color[0], green + color[1], blue + color[2], covered + 1
            if covered:
                alpha = covered * 255 // SUPERSAMPLING**2
                pixels += bytes((blue // covered, green // covered, red // covered, alpha))
            else:
                pixels += bytes(4)
    return user32.CreateIcon(None, ICON_SIZE, ICON_SIZE, 1, 32, bytes(ICON_SIZE * ICON_SIZE // 8), bytes(pixels))


class TrayIcon:
    def __init__(self) -> None:
        self.procedure = WindowProcedure(self._handle)
        instance = kernel32.GetModuleHandleW(None)
        window_class = WindowClass(procedure=self.procedure, instance=instance, class_name=WINDOW_CLASS)
        user32.RegisterClassW(ctypes.byref(window_class))
        self.window = user32.CreateWindowExW(0, WINDOW_CLASS, "Maustasten", 0, 0, 0, 0, 0, None, None, instance, None)
        self.icons = {state: make_icon(state) for state in (False, True)}
        hotkey_registered = user32.RegisterHotKey(self.window, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VIRTUAL_KEY_M)
        self._notify(NIM_ADD, NIF_MESSAGE | NIF_ICON | NIF_TIP)
        if not hotkey_registered:
            self._notify(NIM_MODIFY, NIF_INFO, f"Das Tastenkürzel {HOTKEY_TEXT} ist bereits belegt.")

    def _notify(self, action: int, flags: int, message: str = "") -> None:
        swapped = maus.is_swapped()
        data = NotifyIconData(size=ctypes.sizeof(NotifyIconData), window=self.window, identifier=1, flags=flags)
        data.callback_message = WM_TRAY
        data.icon = self.icons[swapped]
        data.tip = f"Primäre Maustaste: {maus.describe(swapped)} ({HOTKEY_TEXT})"
        data.info_title, data.info, data.info_flags = "Maustasten", message, NIIF_NOSOUND
        shell32.Shell_NotifyIconW(action, ctypes.byref(data))

    def toggle(self) -> None:
        try:
            maus.set_swapped(not maus.is_swapped())
        except OSError:
            return
        self._notify(NIM_MODIFY, NIF_ICON | NIF_TIP | NIF_INFO, f"Primäre Taste: {maus.describe(maus.is_swapped())}")

    def _menu(self) -> None:
        menu = user32.CreatePopupMenu()
        entries = ((MENU_TOGGLE, f"Maustasten tauschen\t{HOTKEY_TEXT}"), (MENU_SETTINGS, "Fenster öffnen"), (MENU_QUIT, "Beenden"))
        for identifier, text in entries:
            user32.AppendMenuW(menu, 0, identifier, text)
        position = Point()
        user32.GetCursorPos(ctypes.byref(position))
        user32.SetForegroundWindow(self.window)
        choice = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD, position.x, position.y, 0, self.window, None)
        user32.PostMessageW(self.window, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        if choice == MENU_TOGGLE:
            self.toggle()
        elif choice == MENU_SETTINGS:
            _spawn()
        elif choice == MENU_QUIT:
            user32.DestroyWindow(self.window)

    def _handle(self, window, message, word_parameter, long_parameter):
        if message == WM_HOTKEY:
            self.toggle()
            return 0
        if message == WM_TRAY:
            event = long_parameter & 0xFFFF
            if event == WM_LBUTTONUP:
                self.toggle()
            elif event == WM_RBUTTONUP:
                self._menu()
            return 0
        if message == WM_CLOSE:
            user32.DestroyWindow(window)
            return 0
        if message == WM_DESTROY:
            self._notify(NIM_DELETE, 0)
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(window, message, word_parameter, long_parameter)

    def run(self) -> None:
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        for icon in self.icons.values():
            user32.DestroyIcon(icon)


def run() -> None:
    """Läuft bis zum Beenden über das Menü; je Benutzer höchstens eine Instanz."""
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        return
    TrayIcon().run()
