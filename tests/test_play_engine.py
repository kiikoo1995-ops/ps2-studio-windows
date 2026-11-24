import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ps2studio.play_engine import build_play_command, start_play, LaunchError, find_bundled_play, find_legacy_mesa, start_play_settings


class PlayEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.exe = self.root / "Play.exe"
        self.disc = self.root / "Game with spaces.iso"
        self.exe.touch()
        self.disc.touch()

    def test_command(self):
        self.assertEqual(build_play_command(self.exe, self.disc),
                         [str(self.exe.resolve()), "--disc", str(self.disc.resolve())])

    def test_fullscreen(self):
        self.assertEqual(build_play_command(self.exe, self.disc, fullscreen=True)[-1], "--fullscreen")

    def test_missing_executable(self):
        with self.assertRaises(LaunchError):
            build_play_command(self.root / "missing.exe", self.disc)

    def test_missing_disc(self):
        with self.assertRaises(LaunchError):
            build_play_command(self.exe, self.root / "missing.iso")

    def test_unsupported_format(self):
        disc = self.root / "game.txt"
        disc.touch()
        with self.assertRaises(LaunchError):
            build_play_command(self.exe, disc)

    @patch("ps2studio.play_engine.subprocess.Popen")
    def test_process(self, popen):
        self.assertIs(start_play(self.exe, self.disc), popen.return_value)
        popen.assert_called_once_with(build_play_command(self.exe, self.disc),
                                      cwd=str(self.root.resolve()), shell=False,
                                      env=dict(os.environ, QT_OPENGL="desktop"))

    @patch("ps2studio.play_engine.subprocess.Popen", side_effect=OSError("test"))
    def test_process_error(self, popen):
        with self.assertRaises(LaunchError):
            start_play(self.exe, self.disc)

    def test_bundled_engine_missing(self):
        self.assertIsNone(find_bundled_play(self.root))

    def test_bundled_engine_found(self):
        engine = self.root / "engine" / "play" / "Play.exe"
        engine.parent.mkdir(parents=True)
        engine.touch()
        self.assertEqual(find_bundled_play(self.root), engine)

    def test_separate_graphics_modes(self):
        native = self.root / "engine" / "play" / "Play.exe"
        mesa = self.root / "engine" / "play-mesa" / "Play.exe"
        for exe in (native, mesa):
            exe.parent.mkdir(parents=True)
            exe.touch()
        (mesa.parent / "opengl32.dll").touch()
        self.assertEqual(find_bundled_play(self.root), native)
        self.assertEqual(find_bundled_play(self.root, software=True), mesa)
        self.assertIsNone(find_legacy_mesa(self.root))

    def test_legacy_mesa_not_mislabeled_native(self):
        native = self.root / "engine" / "play" / "Play.exe"
        native.parent.mkdir(parents=True)
        native.touch()
        (native.parent / "opengl32.dll").touch()
        self.assertIsNone(find_bundled_play(self.root))
        self.assertEqual(find_legacy_mesa(self.root), native)
        self.assertIsNone(find_bundled_play(self.root, software=True))

    def test_incomplete_software_package(self):
        mesa = self.root / "engine" / "play-mesa" / "Play.exe"
        mesa.parent.mkdir(parents=True)
        mesa.touch()
        self.assertIsNone(find_bundled_play(self.root, software=True))

    @patch("ps2studio.play_engine.subprocess.Popen")
    def test_open_real_settings_without_disc(self, popen):
        self.assertIs(start_play_settings(self.exe), popen.return_value)
        popen.assert_called_once_with([str(self.exe.resolve())], cwd=str(self.root.resolve()),
                                      shell=False, env=dict(os.environ, QT_OPENGL="desktop"))

    def test_missing_settings_engine(self):
        with self.assertRaises(LaunchError):
            start_play_settings(self.root / "missing.exe")
