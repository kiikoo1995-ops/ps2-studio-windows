"""Small, locally stored settings file. No accounts, telemetry or cloud access."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import json
import os
from pathlib import Path


class ConfigError(Exception):
    """Raised for malformed or inaccessible configuration."""


def default_config_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return root / "PS2Studio" / "settings.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ps2studio" / "settings.json"


@dataclass
class AppConfig:
    pcsx2_path: str = ""
    game_directories: list[str] = field(default_factory=list)
    fullscreen: bool = False
    recursive: bool = True
    favorites: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: object) -> "AppConfig":
        if not isinstance(data, dict):
            raise ConfigError("El archivo de ajustes debe contener un objeto JSON.")
        exe = data.get("pcsx2_path", "")
        dirs = data.get("game_directories", [])
        fullscreen = data.get("fullscreen", False)
        recursive = data.get("recursive", True)
        favorites = data.get("favorites", [])
        if not isinstance(exe, str):
            raise ConfigError("pcsx2_path debe ser texto.")
        if not isinstance(dirs, list) or any(not isinstance(d, str) for d in dirs):
            raise ConfigError("game_directories debe ser una lista de rutas.")
        if not isinstance(favorites, list) or any(not isinstance(value, str) or not value for value in favorites):
            raise ConfigError("favorites debe ser una lista de rutas no vacías.")
        if not isinstance(fullscreen, bool) or not isinstance(recursive, bool):
            raise ConfigError("fullscreen y recursive deben ser booleanos.")
        return cls(pcsx2_path=exe, game_directories=list(dict.fromkeys(dirs)),
                   fullscreen=fullscreen, recursive=recursive,
                   favorites=list(dict.fromkeys(favorites)))


class ConfigStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            return AppConfig.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, ConfigError) as exc:
            raise ConfigError(f"No se pudo leer {self.path}: {exc}") from exc

    def save(self, config: AppConfig) -> None:
        """Write temporary file then replace to reduce risk of truncated settings."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        try:
            temporary.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        except OSError as exc:
            raise ConfigError(f"No se pudieron guardar los ajustes: {exc}") from exc
