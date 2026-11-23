from pathlib import Path
import tempfile
import unittest

from ps2studio.cover_art import CoverError, suggested_cover, validate_cover


class CoverTests(unittest.TestCase):
    def test_same_name_cover(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game = root / "Example.iso"
            game.write_bytes(b"test")
            art = root / "Example.png"
            art.write_bytes(b"test")
            self.assertEqual(suggested_cover(game), art.resolve())
            self.assertEqual(validate_cover(art), art.resolve())

    def test_no_cover_and_invalid_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game = root / "Example.iso"
            game.write_bytes(b"test")
            self.assertIsNone(suggested_cover(game))
            with self.assertRaises(CoverError):
                validate_cover(root / "nope.png")
            bad = root / "wrong.jpg"
            bad.write_bytes(b"test")
            with self.assertRaises(CoverError):
                validate_cover(bad)

    def test_oversized_art_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            large = Path(folder) / "huge.png"
            with large.open("wb") as output:
                output.truncate(8 * 1024 * 1024 + 1)
            with self.assertRaises(CoverError):
                validate_cover(large)
