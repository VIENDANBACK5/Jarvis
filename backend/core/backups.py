"""Pre-write snapshots.

Before the agent overwrites or edits a file we copy the current bytes into
``.jarvis/backups/``. This is deliberately *not* git: the existing
``GitCheckpointManager`` commits into the user's repository and rolls back with
``git reset --hard`` + ``git clean -fd``, which is far too destructive to run
implicitly on every edit. A plain file copy is recoverable and touches nothing
the user cares about.

Failure to snapshot is logged, never fatal -- a read-only backup directory must
not block the edit the user just approved.
"""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(".jarvis") / "backups"
#: Keep the directory from growing without bound over a long session.
MAX_BACKUPS = 200


def backup_root(workspace: Path) -> Path:
    return workspace / BACKUP_DIR


def snapshot(path: Path, workspace: Path) -> Optional[Path]:
    """Copy ``path`` into the backup directory. Returns the copy, or None."""
    if not path.is_file():
        return None

    try:
        root = backup_root(workspace)
        root.mkdir(parents=True, exist_ok=True)
        try:
            relative = path.resolve().relative_to(workspace.resolve())
        except ValueError:
            relative = Path(path.name)
        # Flatten the path so the backup dir stays one level deep and there is
        # no chance of a name colliding with a directory.
        stamp = time.strftime("%Y%m%d-%H%M%S")
        flat = str(relative).replace("/", "__").replace("\\", "__")
        target = root / f"{stamp}__{flat}"
        counter = 1
        while target.exists():
            target = root / f"{stamp}-{counter}__{flat}"
            counter += 1
        shutil.copy2(path, target)
        _prune(root)
        return target
    except OSError as exc:
        logger.warning("Could not back up %s: %s", path, exc)
        return None


def _prune(root: Path) -> None:
    try:
        entries: List[Path] = sorted(
            (p for p in root.iterdir() if p.is_file()),
            key=lambda p: p.stat().st_mtime,
        )
    except OSError:
        return
    for stale in entries[:-MAX_BACKUPS] if len(entries) > MAX_BACKUPS else []:
        try:
            stale.unlink()
        except OSError:
            pass
