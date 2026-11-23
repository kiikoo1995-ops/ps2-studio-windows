"""Discover local PS2 disc images without modifying their contents."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

IMAGE_EXTENSIONS = frozenset({".iso", ".chd", ".cso", ".zso", ".gz", ".cue", ".bin", ".mdf"})


@dataclass(frozen=True)
class Game:
    title: str
    path: Path
    size_bytes: int

    @property
    def format(self) -> str:
        return self.path.suffix[1:].upper()

    @property
    def size_label(self) -> str:
        return f"{self.size_bytes / (1024 ** 3):.2f} GB" if self.size_bytes >= 1024**3 else f"{self.size_bytes / (1024 ** 2):.1f} MB"


def _is_disc_image(path: Path) -> bool:
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        return False
    # A cue sheet and its associated .bin are one game, not two games.
    if path.suffix.lower() == ".bin" and any(
        candidate.exists() for candidate in (path.with_suffix(".cue"), path.with_suffix(".CUE"))
    ):
        return False
    return True


def scan_games(directories: list[str], *, recursive: bool = True) -> list[Game]:
    """List supported files, deduplicate overlapping roots, skip unreadable files."""
    found: list[Game] = []
    seen: set[str] = set()
    for directory in directories:
        root = Path(directory).expanduser()
        if not root.is_dir():
            continue
        if recursive:
            paths = (Path(parent) / file for parent, _, files in os.walk(root, followlinks=False) for file in files)
        else:
            try:
                paths = (entry for entry in root.iterdir() if entry.is_file())
            except OSError:
                continue
        for path in paths:
            try:
                if not _is_disc_image(path) or not path.is_file():
                    continue
                normalized = os.path.normcase(str(path.resolve()))
                if normalized in seen:
                    continue
                game = Game(title=path.stem.replace("_", " ").strip(), path=path.resolve(), size_bytes=path.stat().st_size)
            except (OSError, ValueError):
                continue
            seen.add(normalized)
            found.append(game)
    return sorted(found, key=lambda game: (game.title.casefold(), str(game.path).casefold()))


def filter_games(
    games: list[Game], query: str, *,
    favorite_paths: set[str] | None = None,
    favorites_only: bool = False,
) -> list[Game]:
    """Filter by title and optionally by paths saved as favorites."""
    q = query.casefold().strip()
    selected = [game for game in games if q in game.title.casefold()] if q else list(games)
    if favorites_only:
        keys = favorite_paths or set()
        selected = [game for game in selected if favorite_key(game.path) in keys]
    return selected


def favorite_key(path: str | Path) -> str:
    """Stable local identity for a file across overlapping scan roots."""
    return os.path.normcase(str(Path(path).expanduser().resolve()))
