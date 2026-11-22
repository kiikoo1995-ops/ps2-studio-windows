from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from ps2studio.launcher import LaunchError, build_command, start_game


class LauncherTests(unittest.TestCase):
    def make_files(self, root):
        exe = Path(root) / "pcsx2-qt.exe"
        game = Path(root) / "Juego 2; && extra.iso"
        exe.write_bytes(b"demo")
        game.write_bytes(b"demo")
        return exe, game

    def test_command_uses_documented_flags_and_separate_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            args = build_command(exe, game, fullscreen=True)
            self.assertEqual(args, [str(exe.resolve()), "-batch", "-fullscreen", "--", str(game.resolve())])

    def test_windowed_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            self.assertNotIn("-fullscreen", build_command(exe, game))

    def test_unexpected_executable_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            exe.rename(Path(folder) / "other.exe")
            with self.assertRaises(LaunchError):
                build_command(Path(folder) / "other.exe", game)

    def test_missing_game_and_wrong_format_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            with self.assertRaises(LaunchError):
                build_command(exe, Path(folder) / "missing.iso")
            invalid = Path(folder) / "not.txt"
            invalid.write_text("no")
            with self.assertRaises(LaunchError):
                build_command(exe, invalid)

    @patch("ps2studio.launcher.subprocess.Popen")
    def test_process_called_without_shell(self, popen):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            start_game(exe, game, fullscreen=True)
            args, kwargs = popen.call_args
            self.assertEqual(args[0][-2:], ["--", str(game.resolve())])
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["cwd"], str(exe.resolve().parent))

    @patch("ps2studio.launcher.subprocess.Popen", side_effect=OSError("not executable"))
    def test_process_error_is_wrapped(self, _):
        with tempfile.TemporaryDirectory() as folder:
            exe, game = self.make_files(folder)
            with self.assertRaises(LaunchError):
                start_game(exe, game)
