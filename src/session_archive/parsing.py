"""Low-level helpers for reading Claude Code ``.jsonl`` transcript files."""
import json
import re
from datetime import datetime


def iter_records(path):
    """Yield every JSON object in a transcript, silently skipping broken lines."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def text_of(content):
    """``message.content`` (a string or a list of blocks) -> plain text.

    Tool calls, tool results and thinking blocks are ignored.
    """
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            out.append(block.get("text", ""))
    return "\n".join(out)


def strip_reminders(text):
    """Remove ``<system-reminder>`` blocks injected by the harness."""
    return re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S).strip()


def epoch(ts):
    """ISO-8601 timestamp (``...Z`` allowed) -> epoch seconds, or ``None``."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def clean_title(text):
    """Collapse whitespace and drop paste markers so a message can serve as a title."""
    text = re.sub(r"</?pasted_content[^>]*>", "", text)
    return re.sub(r"\s+", " ", text).strip()
