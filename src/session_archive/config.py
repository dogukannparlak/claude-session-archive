"""Paths and tunables. Nothing here touches the filesystem at import time."""
import os
from pathlib import Path

DEFAULT_PORT = 8765

# Gaps between two messages longer than this are treated as idle time
# and are not counted towards a session's "active" duration.
IDLE_SECONDS = 15 * 60

# Characters kept per tool input / tool result / message in the transcript API.
MAX_TOOL_INPUT = 3000
MAX_TOOL_RESULT = 4000
MAX_MESSAGE = 6000


def projects_dir(override=None):
    """Directory that holds Claude Code transcripts: ``<config dir>/projects``.

    Resolution order: explicit ``override``, ``$CLAUDE_CONFIG_DIR``, ``~/.claude``.
    """
    if override:
        return Path(override).expanduser()
    base = os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")
    return Path(base).expanduser() / "projects"
