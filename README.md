# Windows-Werkzeuge

Zwei kleine, eigenständige Werkzeuge für Windows mit einheitlicher Oberfläche (hell/dunkel nach Systemeinstellung, hochauflösend, ohne Fremdabhängigkeiten):

- **Ordnergrößen** – zeigt, welche Dateien und Unterordner den meisten Speicher belegen.
- **Maustasten** – vertauscht primäre und sekundäre Maustaste, per Fenster oder Kommandozeile.

![Ordnergrößen](docs/ordnergroessen-dunkel.png)

## Voraussetzungen

**Ohne Installation:** `Ordnergroessen.exe` und `Maustasten.exe` aus den [Releases](https://github.com/Pal-Tomer/Windows-Werkzeuge/releases) laden und starten – weder Python noch weitere Pakete sind nötig. Die Kommandozeilen-Schalter der Maustasten gelten ebenso für die `.exe`.

**Aus dem Quelltext:** Windows 10/11 und Python 3.10 oder neuer (nur Standardbibliothek).

```
git clone https://github.com/Pal-Tomer/Windows-Werkzeuge.git
cd Windows-Werkzeuge
```

## Ordnergrößen

```
pythonw ordnergroessen.pyw
```

- Größen werden im Hintergrund ermittelt und erscheinen, sobald sie feststehen.
- Sortierung per Klick auf die Spaltenköpfe; Doppelklick auf einen Ordner öffnet diesen.
- Verknüpfungen und Junctions werden nicht verfolgt, nicht lesbare Pfade übersprungen.
- Export der Ansicht als CSV (Semikolon, UTF-8 mit BOM, Größe in Bytes) für Excel.

![Ordnergrößen, hell](docs/ordnergroessen-hell.png)

## Maustasten

```
pythonw maustasten_tausch.pyw
```

Ohne Fenster, etwa für ein Tastenkürzel oder eine Verknüpfung:

```
python -m werkzeuge.maustasten --wechseln   # Zustand umschalten
python -m werkzeuge.maustasten --links      # linke Taste primär
python -m werkzeuge.maustasten --rechts     # rechte Taste primär
python -m werkzeuge.maustasten --status
```

Die Umstellung erfolgt über die Windows-Schnittstelle `SystemParametersInfo`; sie wirkt sofort, ohne Registry-Eingriff und ohne Neuanmeldung, und bleibt dauerhaft erhalten.

![Maustasten](docs/maustasten-hell.png)

## Tests

```
python -m unittest discover -s tests -t .
python erstellen.py   # baut die beiden .exe-Dateien (benötigt PyInstaller)
```

## Lizenz

MIT, siehe [LICENSE](LICENSE).
