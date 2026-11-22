"""Safe subprocess integration with an independently installed PCSX2 binary."""
from __future__ import annotations

from pathlib import Path
import subprocess

from .library import IMAGE_EXTENSIONS


class LaunchError(Exception):
    """Could not validate the selected game or emulator."""


def build_command(executable: str | Path, game: str | Path, *, fullscreen: bool = False) -> list[str]:
    exe = Path(executable).expanduser()
    disc = Path(game).expanduser()
    if not exe.is_file() or exe.name.lower() not in {"pcsx2-qt.exe", "pcsx2.exe"}:
        raise LaunchError("Selecciona el archivo pcsx2-qt.exe (o pcsx2.exe) de PCSX2.")
    if not disc.is_file() or disc.suffix.lower() not in IMAGE_EXTENSIONS:
        raise LaunchError("El juego seleccionado no existe o no tiene un formato admitido.")
    # Each item is an argument: no shell expansion or command injection.
    return [str(exe.resolve()), "-batch", *(["-fullscreen"] if fullscreen else []), "--", str(disc.resolve())]


def start_game(executable: str | Path, game: str | Path, *, fullscreen: bool = False) -> subprocess.Popen:
    command = build_command(executable, game, fullscreen=fullscreen)
    try:
        return subprocess.Popen(command, cwd=str(Path(command[0]).parent), shell=False)
    except OSError as exc:
        raise LaunchError(f"No se pudo iniciar PCSX2: {exc}") from exc
