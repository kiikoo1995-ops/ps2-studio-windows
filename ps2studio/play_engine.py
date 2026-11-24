"""Experimental Play! process adapter; not yet wired into the UI."""
from pathlib import Path
import subprocess

from .launcher import LaunchError

# Conservative initial scope; other formats require integration testing.
PLAY_EXTENSIONS = frozenset({".iso"})


def build_play_command(executable: str | Path, game: str | Path, *, fullscreen: bool = False) -> list[str]:
    exe = Path(executable).expanduser()
    disc = Path(game).expanduser()
    if not exe.is_file() or exe.name.lower() != "play.exe":
        raise LaunchError("No se encuentra el ejecutable Play.exe.")
    if not disc.is_file() or disc.suffix.lower() not in PLAY_EXTENSIONS:
        raise LaunchError("La integración experimental requiere una imagen ISO existente.")
    return [str(exe.resolve()), "--disc", str(disc.resolve()), *(["--fullscreen"] if fullscreen else [])]


def start_play(executable: str | Path, game: str | Path, *, fullscreen: bool = False) -> subprocess.Popen:
    command = build_play_command(executable, game, fullscreen=fullscreen)
    try:
        return subprocess.Popen(command, cwd=str(Path(command[0]).parent), shell=False)
    except OSError as exc:
        raise LaunchError(f"No se pudo iniciar Play!: {exc}") from exc
