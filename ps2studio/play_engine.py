"""Experimental Play! process adapter; not yet wired into the UI."""
from pathlib import Path
import subprocess
import sys

class LaunchError(Exception):
    """Could not validate or launch the bundled Play! engine."""

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


def find_bundled_play(root: Path | None = None) -> Path | None:
    """Locate only the engine shipped alongside PS2 Studio, not PATH installs."""
    if root is None:
        root = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent)
    candidate = root / "engine" / "play" / "Play.exe"
    return candidate if candidate.is_file() else None
