"""Turn one transcript file into the message list the UI renders."""
import json

from . import config
from .classify import classify
from .parsing import iter_records, strip_reminders, text_of


def build_transcript(path):
    """Return ``[{role, kind, label, ts, model, parts}]`` for a session file.

    ``parts`` items: ``{k: "text"|"tool"|"result", ...}``. Tool results are kept as
    separate parts so the frontend can pair them with their ``tool_use`` by id.
    Sidechain (sub-agent) records are skipped.
    """
    messages = []
    for rec in iter_records(path):
        role = rec.get("type")
        if role not in ("user", "assistant") or rec.get("isSidechain"):
            continue
        msg = rec.get("message", {})
        content = msg.get("content")
        parts = []
        kind, label = role, ""

        if role == "user":
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
            texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    c = b.get("content")
                    parts.append({
                        "k": "result",
                        "tid": b.get("tool_use_id"),
                        "err": bool(b.get("is_error")),
                        "v": (c if isinstance(c, str) else text_of(c))[: config.MAX_TOOL_RESULT],
                    })
            if texts:
                kind, label, txt = classify(rec, "\n".join(texts))
                if txt:
                    parts.append({"k": "text", "v": txt[: config.MAX_MESSAGE]})
        else:
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    txt = strip_reminders(b.get("text", ""))
                    if txt:
                        parts.append({"k": "text", "v": txt})
                elif b.get("type") == "tool_use":
                    inp = b.get("input")
                    parts.append({
                        "k": "tool",
                        "id": b.get("id"),
                        "name": b.get("name", "?"),
                        "v": json.dumps(inp or {}, ensure_ascii=False, indent=1)[: config.MAX_TOOL_INPUT],
                        "in": inp if isinstance(inp, dict) else {},
                    })

        if parts:
            messages.append({
                "role": role,
                "kind": kind,
                "label": label,
                "ts": rec.get("timestamp", ""),
                "model": msg.get("model", ""),
                "parts": parts,
            })
    return messages
