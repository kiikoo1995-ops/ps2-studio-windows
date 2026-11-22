from pathlib import Path
import tempfile
import unittest

from ps2studio.library import filter_games, scan_games


class LibraryTests(unittest.TestCase):
    def test_disc_formats_and_ignore_unrelated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("Juego.iso", "Otro.CHD", "archivo.cso", "PS2.zso", "original.bin", "notas.txt"):
                (root / name).write_bytes(b"test")
            games = scan_games([folder])
            self.assertEqual({g.path.suffix.lower() for g in games}, {".iso", ".chd", ".cso", ".zso", ".bin"})
            self.assertEqual(len(games), 5)

    def test_overlapping_roots_do_not_duplicate_games(self):
        with tempfile.TemporaryDirectory() as folder:
            nested = Path(folder) / "nested"
            nested.mkdir()
            (nested / "game.iso").write_bytes(b"x")
            self.assertEqual(len(scan_games([folder, str(nested), folder])), 1)

    def test_recursive_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            nested = Path(folder) / "sub"
            nested.mkdir()
            (nested / "hidden.iso").write_bytes(b"x")
            self.assertEqual(len(scan_games([folder], recursive=False)), 0)
            self.assertEqual(len(scan_games([folder], recursive=True)), 1)

    def test_ignore_bin_if_matching_cue_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "DISC.bin").write_bytes(b"x")
            (root / "DISC.cue").write_text('FILE "DISC.bin" BINARY')
            self.assertEqual([g.format for g in scan_games([folder])], ["CUE"])

    def test_filter_case_insensitive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "Gran_Juego.iso").write_bytes(b"x")
            (root / "otro.iso").write_bytes(b"x")
            games = scan_games([folder])
            result = filter_games(games, "GRAN JUEGO")
            self.assertEqual([g.title for g in result], ["Gran Juego"])

    def test_nonexistent_directory(self):
        self.assertEqual(scan_games(["/this/is/an/unlikely/missing/folder"]), [])
