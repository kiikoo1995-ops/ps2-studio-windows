import json
from pathlib import Path
import tempfile
import unittest

from ps2studio.config import AppConfig, ConfigError, ConfigStore


class ConfigTests(unittest.TestCase):
    def test_new_config_has_safe_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            config = ConfigStore(Path(folder) / "missing.json").load()
            self.assertFalse(hasattr(config, "pcsx2_path"))
            self.assertEqual(config.game_directories, [])
            self.assertFalse(config.fullscreen)
            self.assertTrue(config.recursive)
            self.assertEqual(config.favorites, [])

    def test_roundtrip_unicode_spaces(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ConfigStore(Path(folder) / "nested" / "settings.json")
            original = AppConfig(game_directories=["D:/Juegos PS2", "D:/Niñez"], fullscreen=True, recursive=False)
            store.save(original)
            self.assertEqual(store.load(), original)

    def test_bad_json_is_error_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ConfigError):
                ConfigStore(path).load()
            self.assertEqual(path.read_text(), "{broken")

    def test_invalid_types_rejected(self):
        for payload in ({"game_directories": "not a list"}, {"fullscreen": 1}, {"favorites": "game.iso"}, {"favorites": [""]}, []):
            with self.subTest(payload=payload):
                with self.assertRaises(ConfigError):
                    AppConfig.from_dict(payload)

    def test_duplicate_directories_removed(self):
        cfg = AppConfig.from_dict({"game_directories": ["a", "a", "b"]})
        self.assertEqual(cfg.game_directories, ["a", "b"])

    def test_favorites_roundtrip_and_old_config(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ConfigStore(Path(folder) / "settings.json")
            older = {"pcsx2_path": "", "game_directories": ["D:/PS2"], "fullscreen": False, "recursive": True}
            store.path.write_text(json.dumps(older), encoding="utf-8")
            cfg = store.load()
            self.assertEqual(cfg.favorites, [])
            self.assertEqual(cfg.game_directories, ["D:/PS2"])
            self.assertFalse(hasattr(cfg, "pcsx2_path"))
            cfg.favorites = ["D:/PS2/Juego.iso", "D:/PS2/Otro.chd"]
            store.save(cfg)
            self.assertEqual(store.load().favorites, cfg.favorites)
            self.assertNotIn("pcsx2_path", json.loads(store.path.read_text(encoding="utf-8")))

    def test_local_covers_are_optional_and_persisted(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ConfigStore(Path(folder) / "config.json")
            older = AppConfig.from_dict({"game_directories": ["D:/Juegos"]})
            self.assertEqual(older.covers, {})
            older.covers = {"D:/Juegos/game.iso": "D:/Caratulas/game.png"}
            store.save(older)
            self.assertEqual(store.load().covers, older.covers)
            with self.assertRaises(ConfigError):
                AppConfig.from_dict({"covers": {"game.iso": 42}})

    def test_duplicate_favorite_paths_removed(self):
        cfg = AppConfig.from_dict({"favorites": ["a.iso", "a.iso", "b.chd"]})
        self.assertEqual(cfg.favorites, ["a.iso", "b.chd"])
