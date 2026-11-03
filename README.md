# Session Archive

A local, **read-only** web viewer for your [Claude Code](https://claude.com/claude-code)
session history. It reads the transcripts Claude Code already stores on your machine and shows
them as a searchable, chat-style archive in your browser. No dependencies, no account, nothing
leaves your computer.

[Türkçe README](README.tr.md)

## Why

`claude --resume` is great for picking a session up again, but not for *finding* something:
you can't search inside conversations, see how long a task really took, or read an old
session without resuming it. Session Archive fills that gap.

## Features

- **Same titles as `claude --resume`**: reads the `ai-title` / `custom-title` records
  (fallback: your first message).
- **Chat-style view**: Markdown, code blocks with copy buttons, and collapsible tool-call
  cards (`● Bash(ls -la)`) paired with their results.
- **"Did I write this?"**: skill bodies, IDE context, task notifications, sub-agent reports
  and compaction summaries are stored as *user* records but are not yours. They are collapsed
  under a "not written by you" note instead of looking like your messages.
- **Full-text search** across every session, with highlighted snippets, plus a folder filter.
- **Real timeline**: first → last message, total span, and *active time* (gaps over 15
  minutes are ignored), so "82 h" does not pretend you worked 82 hours.
- Branch and file size per session, like the `/resume` picker.
- Resizable, collapsible sidebar (drag, double-click to reset, `Ctrl/⌘+B`).
- English and Turkish UI (auto-detected, switch with the button in the sidebar).
- Per-session JSON export and a one-click copy of the `cd … && claude --resume <id>` command.

## Quick start

Requires Python 3.9+. No packages to install.

```bash
git clone https://github.com/<you>/claude-session-archive.git
cd claude-session-archive
PYTHONPATH=src python3 -m session_archive      # or: make run
```

It opens `http://127.0.0.1:8765/`. Stop it with `Ctrl+C`.

Or install it:

```bash
pip install .
session-archive
```

### Options

| Flag | Meaning |
|---|---|
| `--port N` | Port to listen on (default `8765`) |
| `--projects-dir PATH` | Transcript folder. Default: `$CLAUDE_CONFIG_DIR/projects`, else `~/.claude/projects` |
| `--no-open` | Don't open the browser automatically |
| `--version` | Print the version |

### Keyboard

| Key | Action |
|---|---|
| `/` | Focus search |
| `↑` / `↓` (in search) | Move between sessions |
| `Esc` | Leave the search box |
| `Ctrl/⌘ + B` | Hide / show the sidebar |

## Privacy and security

Transcripts can contain code, secrets and personal data. The viewer is built to keep them local:
loopback-only server, Host-header check against DNS rebinding, strict CSP, read-only API.
There is intentionally no option to listen on other interfaces. Read [SECURITY.md](SECURITY.md)
before changing that, and never commit transcripts or screenshots of them.

## How it works

Pure standard-library Python serves a small JSON API and a plain ES-module frontend (no build
step). Details and the transcript format notes are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
and [docs/TRANSCRIPT_FORMAT.md](docs/TRANSCRIPT_FORMAT.md).

> The `.jsonl` format is not a public, stable API. A Claude Code update can change it; the
> parser is defensive, but if something looks off please open an issue.

## Development

```bash
make test    # unit tests (stdlib unittest)
make lint    # compile all sources
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE). Not affiliated with or endorsed by Anthropic.
