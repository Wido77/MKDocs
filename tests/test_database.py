import tempfile
import unittest
from pathlib import Path

from argos.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "argos.sqlite3")
        self.database.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_creates_authorized_investigation(self) -> None:
        investigation = self.database.create_investigation("Portal de ejemplo", "Comprobación pública.", "https://ejemplo.es", True)
        self.assertEqual(investigation["title"], "Portal de ejemplo")
        self.assertEqual(len(self.database.list_investigations()), 1)

    def test_requires_authorization(self) -> None:
        with self.assertRaisesRegex(ValueError, "confirmar"):
            self.database.create_investigation("Prueba", "", "ejemplo.es", False)
