# Architecture

```
~/.claude/projects/<project>/<session-id>.jsonl      (written by Claude Code, never by us)
        │
        ▼  parsing.py   iter_records, text_of, strip_reminders, epoch
        ▼  classify.py  did the human write this user record?
        ▼
  store.py (SessionStore)          transcript.py (build_transcript)
   - summaries (title, branch,      - one session → messages for the UI
     span, active time)             - tool_use / tool_result parts with ids
   - full-text search
        │                                  │
        └──────────────┬───────────────────┘
                       ▼  server.py  (127.0.0.1 only, read-only JSON + static files)
                       ▼
        static/ (index.html, app.css, js/*.js ES modules)
```

## Backend (`src/session_archive/`)

| Module | Responsibility |
|---|---|
| `config.py` | Projects directory resolution, idle threshold, size limits |
| `parsing.py` | Defensive `.jsonl` reading; text extraction; timestamps |
| `classify.py` | Separates human-typed messages from harness-injected ones |
| `transcript.py` | Builds the message list for one session |
| `store.py` | Index of all sessions; caches parsed summaries and search text by mtime |
| `server.py` | HTTP handler: Host check, CSP, static whitelist, JSON API |
| `backup.py` | Copy-only backup of desktop-app sessions (selection by `entrypoint` and the app index) |
| `cli.py` | `argparse` entry point (`serve` by default, `backup` subcommand) |

### API

| Endpoint | Returns |
|---|---|
| `GET /api/sessions` | Summaries, newest last-message first |
| `GET /api/session/<id>` | Summary + `messages` |
| `GET /api/session/<id>?raw=1` | The raw records as a JSON array (the export button) |
| `GET /api/search?q=…` | `[{id, snippet, count}]` (query ≥ 2 characters) |

Backend → frontend text is always a stable **key** (`label: "skill_context"`), never a display
string; the frontend translates it.

### Caching

`SessionStore` keeps `(mtime, summary)` and `(mtime, lower-cased text)` per file. A request only
re-parses files that changed. The whole text index lives in memory (a few MB for hundreds of
sessions).

## Frontend (`static/js/`)

Plain ES modules, no bundler: `main.js` (wiring) → `list.js` (sidebar), `chat.js`
(conversation), `panel.js` (resize/collapse), `markdown.js` (tiny renderer), `format.js`,
`i18n.js` (tr/en), `dom.js`, `state.js`.

Rules: every string from a transcript is escaped before it reaches `innerHTML`; user-visible
text goes through `t()`; `localStorage` access is wrapped in try/catch.

## Design decisions

- **Standard library only.** Nothing to install, nothing to audit.
- **No `--host`.** The tool exposes private conversations; listening beyond loopback is out of scope.
- **Active time, not just span.** Gaps over 15 minutes are dropped so a session left open for
  days doesn't look like days of work.
