"""Where a session was started: terminal, Obsidian, VS Code, desktop app, SDK ...

Claude Code records an ``entrypoint`` on every transcript record. The UI shows one icon per
*source* (the stable keys below); unknown entrypoints fall back to ``other`` so a new Claude
Code version never breaks the list.

Obsidian is a heuristic: a terminal plugin inside Obsidian starts a plain ``claude`` process, so
the transcript looks exactly like any other terminal session. We call a ``cli`` session
"obsidian" when its working directory is inside an Obsidian vault (a folder with ``.obsidian``).
A session you started in that folder from another terminal is labelled the same way.
"""
from pathlib import Path

ENTRYPOINT_SOURCES = {
    "cli": "terminal",
    "claude-desktop": "desktop",
    "claude-vscode": "vscode",
    "sdk-cli": "sdk",
    "sdk-ts": "sdk",
    "sdk-py": "sdk",
}

SOURCES = ("desktop", "terminal", "obsidian", "vscode", "sdk", "other")


def in_obsidian_vault(cwd):
    """True if ``cwd`` or one of its parents contains an ``.obsidian`` folder."""
    if not cwd:
        return False
    path = Path(cwd)
    try:
        return any((d / ".obsidian").is_dir() for d in (path, *path.parents))
    except OSError:
        return False


def source_of(entrypoint, cwd=None):
    """``entrypoint`` (or ``None``) and the working directory -> one of :data:`SOURCES`."""
    source = ENTRYPOINT_SOURCES.get(entrypoint, "other")
    if source == "terminal" and in_obsidian_vault(cwd):
        return "obsidian"
    return source
