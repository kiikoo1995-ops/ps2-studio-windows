"""Best-effort local PCSX2 detection. Never downloads or executes software."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Callable, Mapping

EXECUTABLE_NAMES = ("pcsx2-qt.exe", "pcsx2.exe")
INSTALL_FOLDERS = ("PCSX2", "PCSX2 Nightly", "PCSX2 Stable")


def find_pcsx2(
    *,
    environ: Mapping[str, str] | None = None,
    path_lookup: Callable[[str], str | None] | None = None,
) -> str | None:
    """Return a recognized PCSX2 executable from PATH or common Windows locations.

    Detection is advisory: users can always select an executable manually.
    The search only checks known filenames in plausible installation folders.
    """
    env = os.environ if environ is None else environ
    which = shutil.which if path_lookup is None else path_lookup
    candidates: list[Path] = []
    for filename in EXECUTABLE_NAMES:
        discovered = which(filename)
        if discovered:
            candidates.append(Path(discovered))

    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = env.get(variable)
        if not value:
            continue
        base = Path(value).expanduser()
        for folder in INSTALL_FOLDERS:
            for filename in EXECUTABLE_NAMES:
                candidates.append(base / folder / filename)

    seen: set[str] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
            key = os.path.normcase(str(resolved))
            if key in seen:
                continue
            seen.add(key)
            if resolved.name.lower() in EXECUTABLE_NAMES and resolved.is_file():
                return str(resolved)
        except (OSError, ValueError):
            continue
    return None
