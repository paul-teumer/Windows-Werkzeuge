"""Erzeugt die eigenständigen Programme Ordnergroessen.exe und Maustasten.exe (benötigt PyInstaller, nur zum Bauen)."""

import shutil
import subprocess
import sys
from pathlib import Path

ordner = Path(__file__).resolve().parent
zwischen = ordner / "build"
for skript, name in (("ordnergroessen.pyw", "Ordnergroessen"), ("maustasten_tausch.pyw", "Maustasten")):
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--noconfirm", "--clean",
         "--name", name, "--distpath", str(zwischen / "ergebnis"),
         "--workpath", str(zwischen / "arbeit"), "--specpath", str(zwischen),
         str(ordner / skript)],
        check=True,
    )
    (zwischen / "ergebnis" / f"{name}.exe").replace(ordner / f"{name}.exe")
shutil.rmtree(zwischen)
