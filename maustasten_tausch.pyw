import ctypes
import os
import sys

from werkzeuge.maustasten import main

ATTACH_PARENT_PROCESS = -1

if sys.stdout is None:
    # Fensterlose Anwendung: Ausgaben der Kommandozeile in das aufrufende Terminal leiten.
    if ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
        sys.stdout = open("CONOUT$", "w", encoding="utf-8")
        sys.stderr = sys.stdout
    else:
        sys.stdout = sys.stderr = open(os.devnull, "w")

sys.exit(main())
