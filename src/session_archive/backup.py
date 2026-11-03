"""Copy-only backup of Claude Code *app* sessions.

Claude Code removes old transcripts on its own (the ``cleanupPeriodDays`` setting), and that
setting is global: it cannot spare only the sessions you started from the desktop app. This
module copies the sessions you care about into a separate folder that Claude Code never
touches. It only ever **adds or refreshes** files in the destination; it never deletes.

Which sessions count as "app" sessions:

* records whose ``entrypoint`` is ``claude-desktop`` (the desktop app's Code tab), and
* sessions listed in the desktop app's own index (``local_*.json`` files holding a
  ``cliSessionId``), if that index can be found. The app also *adopts* terminal and VS Code
  sessions into that index (``adoptedFromOtherSurface: true``); those are not app sessions and
  are skipped.

Use ``include_all=True`` to back up every session, terminal ones included.
"""
import json
import os
import shutil
from pathlib import Path

from .parsing import iter_records

APP_ENTRYPOINTS = ("claude-desktop",)


def default_app_index():
    """Where the macOS desktop app keeps its session index (may not exist)."""
    return Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"


def default_backup_dir():
    return Path.home() / "Documents" / "claude-session-backup" / "projects"


def indexed_session_ids(index_root):
    """Transcript ids of sessions that were *started* in the desktop app, per its session index."""
    ids = set()
    if not index_root or not Path(index_root).is_dir():
        return ids
    for path in Path(index_root).rglob("local_*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)
            cli_id = entry.get("cliSessionId")
            adopted = entry.get("adoptedFromOtherSurface")
        except (OSError, ValueError, AttributeError):
            continue
        if cli_id and not adopted:
            ids.add(cli_id)
    return ids


def entrypoint_of(path):
    """The ``entrypoint`` of a transcript (first record that has one), or ``None``."""
    for rec in iter_records(path):
        if rec.get("entrypoint"):
            return rec["entrypoint"]
    return None


def select_sessions(projects_dir, index_root=None, include_all=False):
    """Transcript paths to back up."""
    projects_dir = Path(projects_dir)
    indexed = set() if include_all else indexed_session_ids(index_root)
    for path in sorted(projects_dir.glob("*/*.jsonl")):
        if include_all or path.stem in indexed or entrypoint_of(path) in APP_ENTRYPOINTS:
            yield path


def backup(projects_dir, dest, index_root=None, include_all=False, dry_run=False):
    """Copy selected sessions to ``dest/<project>/<id>.jsonl``.

    A file is copied when missing, and refreshed when the source has grown (the session
    continued). Existing destination files are never shrunk or deleted.
    Returns ``{"selected", "copied", "updated", "skipped"}``.
    """
    dest = Path(dest)
    counts = {"selected": 0, "copied": 0, "updated": 0, "skipped": 0}
    for src in select_sessions(projects_dir, index_root, include_all):
        counts["selected"] += 1
        target = dest / src.parent.name / src.name
        if not target.exists():
            action = "copied"
        elif src.stat().st_size > target.stat().st_size:
            action = "updated"
        else:
            counts["skipped"] += 1
            continue
        counts[action] += 1
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        shutil.copy2(src, tmp)
        os.replace(tmp, target)  # atomic: never leaves a half-written backup
    return counts
