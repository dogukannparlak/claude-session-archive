# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-11-04

First version (not published or tagged yet).

### Added
- Local, read-only web viewer for Claude Code transcripts (`~/.claude/projects/*/*.jsonl`).
- Chat-style rendering: Markdown, code blocks with copy buttons, collapsible tool-call cards
  paired with their results.
- Titles identical to `claude --resume` (`ai-title` / `custom-title` records), with a
  fallback to the first human message.
- Separation of what you typed from what the harness injected (skill bodies, IDE context,
  task notifications, sub-agent reports, compaction summaries): the latter is collapsed
  under a "not written by you" note.
- An icon per session source plus a source filter: Claude Code app, terminal, Obsidian terminal
  (heuristic: working directory inside a vault), VS Code, SDK. Claude, Obsidian and VS Code use
  their real logos as SVG files (see `NOTICE.md`).
- Full-text search across all sessions, folder filter, branch and file size per session.
- First/last message dates, total span and active time (gaps over 15 minutes are ignored).
- Resizable, collapsible sidebar (drag, double-click to reset, Ctrl/Cmd+B).
- English and Turkish UI (auto-detected, switchable); dates follow the UI language.
- Theme button (follow system / light / dark), remembered per browser, no flash on load.
- Favicon.
- JSON export of a single session and a copy button for the `claude --resume` command.
- Configuration: `.env` and a JSON config file (`session-archive print-config`); paths and the list
  of sources (label, builtin icon or your own image, rules on entrypoint / working directory) can
  be added, removed and reordered. See `docs/CONFIGURATION.md`.
- `session-archive backup`: copy-only backup of desktop-app sessions (never deletes), so Claude
  Code's age-based cleanup cannot remove them; `--projects-dir` can be repeated to browse live
  and backed-up sessions together.
- `scripts/make_demo_data.py` and `make demo`: synthetic data for screenshots.
- Security: loopback-only server, Host-header check (DNS rebinding), strict CSP,
  whitelisted static files, validated session ids.
- Unit tests (standard library only), CI workflow, contributor and security documents.
