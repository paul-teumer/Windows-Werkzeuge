import tempfile
import unittest
from pathlib import Path

from werkzeuge import maus, ordnergroessen


class FormatSizeTest(unittest.TestCase):
    def test_units_and_decimal_comma(self):
        self.assertEqual(ordnergroessen.format_size(512), "512 B")
        self.assertEqual(ordnergroessen.format_size(1536), "1,5 KB")
        self.assertEqual(ordnergroessen.format_size(5 * 1024**3), "5,0 GB")


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.root, ignore_errors=True))
        (self.root / "datei.bin").write_bytes(b"x" * 100)
        (self.root / "ordner" / "tief").mkdir(parents=True)
        (self.root / "ordner" / "a.bin").write_bytes(b"x" * 40)
        (self.root / "ordner" / "tief" / "b.bin").write_bytes(b"x" * 60)

    def test_directory_size_is_recursive(self):
        self.assertEqual(ordnergroessen.directory_size(str(self.root / "ordner")), 100)

    def test_scan_lists_files_and_folders(self):
        found = {entry.name: (entry.is_directory, entry.size) for entry in ordnergroessen.scan(str(self.root))}
        self.assertEqual(found, {"datei.bin": (False, 100), "ordner": (True, 100)})

    def test_missing_folder_yields_nothing(self):
        self.assertEqual(list(ordnergroessen.scan(str(self.root / "fehlt"))), [])


class MouseTest(unittest.TestCase):
    def test_state_text(self):
        self.assertEqual(maus.describe(True), "Rechts")
        self.assertEqual(maus.describe(False), "Links")

    def test_current_state_is_readable(self):
        self.assertIsInstance(maus.is_swapped(), bool)


if __name__ == "__main__":
    unittest.main()
