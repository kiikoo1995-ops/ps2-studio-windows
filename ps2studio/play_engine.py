"""Process adapter for the bundled experimental Play! engine."""
from pathlib import Path
import os
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


def start_play(executable: str | Path, game: str | Path, *, fullscreen: bool = False,
               profile: str | None = None, vulkan: bool = False) -> subprocess.Popen:
    command = build_play_command(executable, game, fullscreen=fullscreen)
    return _start_command(command, profile=profile, vulkan=vulkan)


def start_play_settings(executable: str | Path) -> subprocess.Popen:
    """Open the real Play! settings interface without booting a disc."""
    exe = Path(executable).expanduser()
    if not exe.is_file() or exe.name.lower() != "play.exe":
        raise LaunchError("No se encuentra el ejecutable Play.exe.")
    return _start_command([str(exe.resolve())])


def graphics_environment(executable: Path, profile: str | None, vulkan: bool = False) -> dict[str, str]:
    env = dict(os.environ, QT_OPENGL="desktop")
    for key in ("PS2STUDIO_RESOLUTION", "PS2STUDIO_RENDERER"):
        env.pop(key, None)
    if profile is None and not vulkan:
        return env
    if not (executable.parent / "ps2studio-profile-v1.txt").is_file():
        raise LaunchError("Este motor no admite perfiles integrados; utiliza sus ajustes de vídeo.")
    software = (executable.parent / "opengl32.dll").is_file()
    scales = {"auto": 1, "speed": 1, "balanced": 2, "quality": 4, "ultra": 8}
    if profile not in scales:
        raise LaunchError("Perfil gráfico desconocido.")
    if vulkan and (software or scales[profile] != 1):
        raise LaunchError("Vulkan experimental requiere GPU nativa y resolución 1x; el escalado alto solo está comprobado como opción OpenGL.")
    env["PS2STUDIO_RESOLUTION"] = str(scales[profile])
    env["PS2STUDIO_RENDERER"] = "vulkan" if vulkan else "opengl"
    return env


def _start_command(command: list[str], *, profile: str | None = None, vulkan: bool = False) -> subprocess.Popen:
    env = graphics_environment(Path(command[0]), profile, vulkan)
    try:
        return subprocess.Popen(command, cwd=str(Path(command[0]).parent), shell=False, env=env)
    except OSError as exc:
        raise LaunchError(f"No se pudo iniciar Play!: {exc}") from exc


def find_bundled_play(root: Path | None = None, *, software: bool = False) -> Path | None:
    """Locate only the engine shipped alongside PS2 Studio, not PATH installs."""
    if root is None:
        root = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent)
    folder = "play-mesa" if software else "play"
    candidate = root / "engine" / folder / "Play.exe"
    if not candidate.is_file():
        return None
    local_gl = (candidate.parent / "opengl32.dll").is_file()
    if software:
        return candidate if local_gl else None
    return candidate if not local_gl else None


def find_legacy_mesa(root: Path | None = None) -> Path | None:
    """Recognize the older single-directory software package."""
    if root is None:
        root = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent)
    candidate = root / "engine" / "play" / "Play.exe"
    return candidate if candidate.is_file() and (candidate.parent / "opengl32.dll").is_file() else None
