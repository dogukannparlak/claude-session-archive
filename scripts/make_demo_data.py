#!/usr/bin/env python3
"""Generate a synthetic Claude Code projects directory for screenshots and demos.

Every conversation, name and path here is made up. Run it, then point the viewer at the output:

    python3 scripts/make_demo_data.py /tmp/demo/projects
    PYTHONPATH=src python3 -m session_archive --projects-dir /tmp/demo/projects
"""
import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODEL = "claude-sonnet-5-5"

PAGINATION_FIX = """The bug is in the query, not the handler. `OFFSET` is applied *before* the join, so orders with several line items are counted once per item:

| Step | What happens | Result |
|---|---|---|
| 1 | `LIMIT 20 OFFSET 20` on `orders JOIN items` | rows 21-40 of the **joined** set |
| 2 | Handler groups rows by `order_id` | fewer than 20 orders, some repeated |

Paginate the orders first, then join:

```python
def list_orders(page: int, size: int = 20):
    page_ids = (
        select(Order.id).order_by(Order.created_at.desc())
        .limit(size).offset((page - 1) * size).subquery()
    )
    return db.query(Order).join(page_ids, Order.id == page_ids.c.id).all()
```

Things I checked:
- no other endpoint uses the same helper
- the index on `created_at` already exists
- page 1 was only correct by luck (no earlier duplicates to skip)"""

HANDLER = '''def list_orders(page, size=20):
    q = db.query(Order).join(Item)          # one row per line item
    return q.limit(size).offset((page - 1) * size).all()
'''

SESSIONS = [
    dict(key="orders", cwd="/home/demo/acme-api", branch="fix/orders-pagination", entry="claude-desktop",
         title="Fix duplicate rows in /orders pagination", ago_h=2.0, turns=[
        ("u", "The /orders endpoint returns duplicate rows when page=2. Can you find out why?"),
        ("a", "I'll start with the handler and the query it builds."),
        ("tool", "Read", {"file_path": "src/orders/handlers.py"}, HANDLER),
        ("tool", "Bash", {"command": "pytest -q tests/test_orders.py"}, "FAILED tests/test_orders.py::test_page_two_has_no_duplicates\n1 failed, 14 passed in 0.82s"),
        ("a", "Found it: `OFFSET` is applied to the joined rows, not to the orders. Want me to fix it and add a regression test?"),
        ("meta", "Base directory for skill: /home/demo/.claude/skills/python-style\n\n# Python style\nPrefer explicit subqueries over implicit joins when paginating. Keep functions under 30 lines."),
        ("u", "Yes, apply it and add the test."),
        ("tool", "Edit", {"file_path": "src/orders/handlers.py", "old_string": "q = db.query(Order).join(Item)", "new_string": "page_ids = select(Order.id)..."}, "The file src/orders/handlers.py has been updated."),
        ("tool", "Bash", {"command": "pytest -q"}, "15 passed in 0.91s"),
        ("a", PAGINATION_FIX),
    ]),
    dict(key="darkmode", cwd="/home/demo/todo-app", branch="feature/dark-mode", entry="cli",
         title="Add a dark mode toggle", ago_h=5.5, turns=[
        ("u", "add a dark mode toggle to the settings page, persist it in localStorage"),
        ("a", "Plan:\n1. Add a `theme` store\n2. Read the saved value on load\n3. Toggle the `data-theme` attribute"),
        ("tool", "Grep", {"pattern": "prefers-color-scheme", "path": "src"}, "src/styles/base.css:12:@media (prefers-color-scheme: dark) {"),
        ("a", "The CSS already follows the system theme, so I only need an override. Implemented in `src/theme.ts`."),
        ("int",),
        ("u", "keep it simple, no new dependency"),
        ("a", "Understood. It is plain DOM and `localStorage`, no dependency added."),
    ]),
    dict(key="parser", cwd="/home/demo/blog-engine", branch="refactor/markdown", entry="claude-vscode",
         title="Refactor the Markdown parser into small passes", ago_h=9, turns=[
        ("u", "split parse_markdown() into block and inline passes"),
        ("tool", "Read", {"file_path": "blog/markdown.py"}, "def parse_markdown(text): ...  # 410 lines"),
        ("a", "The function does three jobs. I'll extract `parse_blocks()` and `parse_inline()` and keep `parse_markdown()` as a thin wrapper."),
        ("note", "<task-notification><task-id>b7q2</task-id><status>completed</status><summary>Background test run finished</summary></task-notification>"),
        ("a", "Background tests finished green after the split."),
    ]),
    dict(key="report", cwd="/home/demo/data-pipeline", branch="main", entry="sdk-cli",
         title="Nightly sales report script", ago_h=14, turns=[
        ("u", "write a script that emails the nightly sales summary as CSV"),
        ("a", "```python\nimport csv, smtplib\n\ndef build_report(rows):\n    ...\n```\nI used the standard library only, so the cron job needs no virtualenv."),
    ]),
    dict(key="migration", cwd="/home/demo/acme-api", branch="main", entry="cli",
         title="Write a migration for the users table", ago_h=27, turns=[
        ("u", "add a nullable `last_login_at` column to users, with a migration"),
        ("tool", "Bash", {"command": "alembic revision -m add_last_login_at"}, "Generating migrations/versions/3f2a_add_last_login_at.py ... done"),
        ("a", "Created the revision. The column is nullable, so no backfill is required and the migration is safe to run online."),
    ]),
    dict(key="docs", cwd="/home/demo/docs-site", branch="docs/contributing", entry="claude-desktop",
         title="Draft the contributing guide", ago_h=30, turns=[
        ("u", "draft a CONTRIBUTING.md for the docs site"),
        ("a", "## Contributing\n\n- Fork and branch from `main`\n- Run `make preview` before opening a PR\n- Keep pages under 800 words\n\nWant a section on translations too?"),
        ("u", "yes, short"),
        ("a", "Added: translations live in `i18n/<lang>/`, and every new page needs an English source first."),
    ]),
    dict(key="flaky", cwd="/home/demo/todo-app", branch="fix/flaky-sync", entry="cli",
         title="Investigate the flaky sync test", ago_h=80, span_h=60, turns=[
        ("u", "test_sync_retries fails about one run in ten, find out why"),
        ("tool", "Bash", {"command": "pytest tests/test_sync.py -x --count=50"}, "FAILED on run 23: assert 3 == 2"),
        ("a", "The retry counter is shared between tests. I suspect the module-level `RETRIES` list."),
        ("gap", 600),
        ("u", "any progress?"),
        ("a", "Confirmed: resetting `RETRIES` in a fixture removes the flakiness (200 runs, 0 failures)."),
        ("gap", 2400),
        ("u", "ok merge it"),
        ("a", "I won't merge or push without your go-ahead. The branch `fix/flaky-sync` is ready for a PR."),
    ]),
    dict(key="vault", cwd="@vault", branch="main", entry="cli",
         title="Summarize this week's meeting notes", ago_h=48, turns=[
        ("u", "summarize the notes in daily/ for this week and list open action items"),
        ("tool", "Bash", {"command": "ls daily | tail -5"}, "2026-11-02.md\n2026-11-03.md\n2026-11-04.md"),
        ("a", "Three open action items:\n1. Send the budget draft to Alex\n2. Book the venue for the offsite\n3. Review the onboarding checklist"),
    ]),
    dict(key="regex", cwd="/home/demo/scratch", branch="", entry=None,
         title="Quick regex help", ago_h=120, turns=[
        ("u", "regex that matches ISO dates like 2026-11-04"),
        ("a", "`\\b\\d{4}-\\d{2}-\\d{2}\\b`. It does not validate the month or day range."),
    ]),
    dict(key="cache", cwd="/home/demo/acme-api", branch="perf/cache", entry="claude-vscode",
         title="Cache expensive price lookups", ago_h=170, turns=[
        ("u", "price lookups hit the DB on every request, add a cache"),
        ("a", "An in-process TTL cache (60 s) is the smallest change. Redis would be better once there is more than one instance."),
    ]),
    dict(key="i18n", cwd="/home/demo/docs-site", branch="main", entry="claude-desktop",
         title="Translate the landing page to Turkish", ago_h=200, turns=[
        ("u", "translate the landing page copy to Turkish, keep the tone friendly"),
        ("a", "Done. I kept product names in English and shortened two headlines that overflowed the hero section."),
    ]),
]


def sid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "session-archive-demo/" + key))


def build(spec, now):
    start = now - timedelta(hours=spec["ago_h"])
    t = start
    sessionid = sid(spec["key"])
    base = {"isSidechain": False, "cwd": spec["cwd"], "sessionId": sessionid}
    if spec["branch"]:
        base["gitBranch"] = spec["branch"]
    if spec["entry"]:
        base["entrypoint"] = spec["entry"]

    def stamp():
        return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    out, n = [], 0

    def rec(role, content, **extra):
        nonlocal n
        n += 1
        r = dict(base, type=role, timestamp=stamp(), uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, "%s/%d" % (sessionid, n))))
        r["message"] = {"role": role, "content": content}
        if role == "assistant":
            r["message"]["model"] = MODEL
        r.update(extra)
        out.append(r)

    for turn in spec["turns"]:
        kind = turn[0]
        if kind == "gap":
            t += timedelta(minutes=turn[1])
            continue
        t += timedelta(minutes=2)
        if kind == "u":
            rec("user", turn[1], origin={"kind": "human"})
        elif kind == "a":
            rec("assistant", [{"type": "text", "text": turn[1]}])
        elif kind == "tool":
            tid = "toolu_" + uuid.uuid5(uuid.NAMESPACE_URL, "%s/%d" % (sessionid, n)).hex[:12]
            rec("assistant", [{"type": "tool_use", "id": tid, "name": turn[1], "input": turn[2]}])
            t += timedelta(seconds=20)
            rec("user", [{"type": "tool_result", "tool_use_id": tid, "content": turn[3]}])
        elif kind == "meta":
            rec("user", turn[1], isMeta=True)
        elif kind == "note":
            rec("user", turn[1], origin={"kind": "task-notification"})
        elif kind == "int":
            rec("user", "[Request interrupted by user]")
    out.append({"type": "ai-title", "aiTitle": spec["title"], "sessionId": sessionid})
    if spec.get("span_h"):  # stretch long sessions: shift the first timestamp back
        pass
    return sessionid, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", help="output projects directory (created if missing)")
    args = ap.parse_args()
    dest = Path(args.dest)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    vault = (dest.parent / "home" / "demo" / "notes-vault").resolve()
    (vault / ".obsidian").mkdir(parents=True, exist_ok=True)  # makes the "Obsidian" source detectable
    for spec in SESSIONS:
        if spec["cwd"] == "@vault":
            spec = dict(spec, cwd=str(vault))
        sessionid, records = build(spec, now)
        folder = dest / spec["cwd"].replace("/", "-")
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / (sessionid + ".jsonl"), "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %d synthetic sessions to %s" % (len(SESSIONS), dest))


if __name__ == "__main__":
    sys.exit(main())
