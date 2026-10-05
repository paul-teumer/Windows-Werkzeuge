"""Zugriff auf die Windows-Einstellung für die Belegung der Maustasten."""

from __future__ import annotations

import ctypes

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
