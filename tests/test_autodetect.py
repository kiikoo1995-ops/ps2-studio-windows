from pathlib import Path
import tempfile
import unittest

from ps2studio.autodetect import find_pcsx2


class AutoDetectTests(unittest.TestCase):
    def test_detects_common_program_files_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "PCSX2" / "pcsx2-qt.exe"
            exe.parent.mkdir()
            exe.write_bytes(b"demo")
            self.assertEqual(find_pcsx2(environ={"ProgramFiles": folder}, path_lookup=lambda _: None), str(exe.resolve()))

    def test_detects_qt_from_path(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "pcsx2-qt.exe"
            exe.write_bytes(b"demo")
            found = find_pcsx2(
                environ={}, path_lookup=lambda name: str(exe) if name == "pcsx2-qt.exe" else None,
            )
            self.assertEqual(found, str(exe.resolve()))

    def test_rejects_unexpected_file_and_missing_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "other.exe"
            exe.write_bytes(b"demo")
            self.assertIsNone(find_pcsx2(environ={}, path_lookup=lambda _: str(exe)))
            self.assertIsNone(find_pcsx2(environ={"ProgramFiles": folder}, path_lookup=lambda _: None))
