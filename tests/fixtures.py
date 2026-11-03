"""Synthetic transcripts. Never put real conversations in the test suite."""
import contextlib
import json
import os
import tempfile
from pathlib import Path

SESSION_ID = "11111111-2222-3333-4444-555555555555"
OTHER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _rec(type_, ts, content, **extra):
    base = {"type": type_, "timestamp": ts, "cwd": "/work/demo", "gitBranch": "main", "isSidechain": False}
    base["message"] = {"role": type_, "content": content}
    base.update(extra)
    return base


def main_session():
    """A session covering every record kind the viewer cares about."""
    return [
        {"type": "ai-title", "aiTitle": "Old title"},
        _rec("user", "2026-01-01T10:00:00.000Z", "<system-reminder>harness noise</system-reminder>\nHello Claude", origin={"kind": "human"}),
        _rec("assistant", "2026-01-01T10:01:00.000Z", [
            {"type": "text", "text": "Sure, listing files."},
            {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "ls"}},
        ], **{}),
        _rec("user", "2026-01-01T10:01:05.000Z", [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "a.txt\nb.txt"}]),
        _rec("user", "2026-01-01T10:02:00.000Z", "Base directory for skill: /x\n...skill body...", isMeta=True),
        _rec("assistant", "2026-01-01T10:02:30.000Z", [{"type": "text", "text": "Done. Needle appears here."}]),
        # 3 hours of idle time, then one more message: must not count as active time
        _rec("user", "2026-01-01T13:02:30.000Z", "[Request interrupted by user]"),
        {"type": "ai-title", "aiTitle": "Final title"},
        # sub-agent records are ignored
        _rec("user", "2026-01-01T13:03:00.000Z", "sidechain text", isSidechain=True),
    ]


def second_session():
    return [
        _rec("user", "2026-01-02T09:00:00.000Z", "Only a first message, no title records", origin={"kind": "human"}),
        _rec("assistant", "2026-01-02T09:00:10.000Z", [{"type": "text", "text": "ok"}]),
    ]


def write_session(root, project, session_id, records):
    folder = Path(root) / project
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (session_id + ".jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.write("not json, must be skipped\n")
    return path


def make_projects_dir():
    """Create a temp projects dir with two sessions. Caller removes it (use addCleanup)."""
    tmp = tempfile.TemporaryDirectory()
    write_session(tmp.name, "-work-demo", SESSION_ID, main_session())
    write_session(tmp.name, "-work-demo", OTHER_ID, second_session())
    return tmp


@contextlib.contextmanager
def isolated_cwd():
    """Run in an empty temp directory so a developer's own ./.env or ./session-archive.json
    (both git-ignored) can never leak into a test. Yields the directory."""
    old = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(old)
