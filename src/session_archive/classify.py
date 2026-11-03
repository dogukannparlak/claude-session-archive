"""Decide who really wrote a "user" record.

Claude Code stores many things under ``type: "user"`` that the person never typed:
skill bodies, IDE context, task notifications, sub-agent reports, compaction
summaries, ... This module separates them so the UI can collapse the noise.
"""
import re

from .parsing import strip_reminders

IDE_TAG = re.compile(r"<(ide_opened_file|ide_selection)>.*?</\1>", re.S)
COMMAND_TAG = re.compile(
    r"<command-message>.*?</command-message>\s*<command-name>(.*?)</command-name>\s*"
    r"(?:<command-args>(.*?)</command-args>)?",
    re.S,
)

# Kinds rendered as small harness notes (collapsed) instead of chat bubbles.
NOTE_KINDS = ("meta", "system")


def classify(record, text):
    """Classify a user record.

    Returns ``(kind, label_key, text)``. ``kind`` is one of ``human``, ``shell``,
    ``command``, ``interrupt``, ``meta`` or ``system``. ``label_key`` is a stable
    identifier the frontend translates (empty for ``human``/``shell``/``command``).
    """
    origin = record.get("origin")
    origin_kind = origin.get("kind") if isinstance(origin, dict) else None
    raw = text.strip()

    if origin_kind == "task-notification":
        return "system", "task_notification", raw
    if origin_kind == "peer":
        return "system", "peer_message", raw
    if origin_kind == "auto-continuation":
        return "system", "auto_continue", raw
    if raw.startswith("[Request interrupted"):
        return "interrupt", "interrupted", raw
    if raw.startswith("This session is being continued"):
        return "system", "session_summary", raw
    if raw.startswith("<bash-input>"):
        m = re.search(r"<bash-input>(.*?)</bash-input>", raw, re.S)
        return "shell", "", (m.group(1) if m else raw).strip()
    if raw.startswith(("<bash-stdout>", "<bash-stderr>")):
        return "meta", "shell_output", raw
    if raw.startswith("<local-command"):
        return "meta", "local_command_output", raw
    m = COMMAND_TAG.match(raw)
    if m:
        return "command", "", (m.group(1) + " " + (m.group(2) or "")).strip()
    if record.get("isMeta"):
        return "meta", ("image_info" if raw.startswith("[Image") else "skill_context"), raw

    clean = strip_reminders(IDE_TAG.sub("", raw))
    if not clean:
        return "meta", "system_context", raw
    return "human", "", clean
