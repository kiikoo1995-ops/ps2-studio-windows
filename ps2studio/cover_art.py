"""User-selected PNG and GIF cover art, kept locally without downloads."""
from __future__ import annotations

from pathlib import Path

SUPPORTED = frozenset({".png", ".gif"})
MAX_BYTES = 8 * 1024 * 1024


class CoverError(ValueError):
    """The cover is missing, too large, or uses an unsupported file format."""


def validate_cover(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.suffix.lower() not in SUPPORTED:
        raise CoverError("Selecciona una imagen PNG o GIF.")
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            raise CoverError("La carátula no es un archivo.")
        if resolved.stat().st_size > MAX_BYTES:
            raise CoverError("La carátula no debe superar 8 MB.")
    except OSError as exc:
        raise CoverError("No se pudo abrir la carátula.") from exc
    return resolved


def suggested_cover(game_path: str | Path) -> Path | None:
    """Find only a user's same-name PNG/GIF in the game directory."""
    game = Path(game_path)
    for suffix in (".png", ".PNG", ".gif", ".GIF"):
        try:
            return validate_cover(game.with_suffix(suffix))
        except (CoverError, OSError, ValueError):
            continue
    return None
