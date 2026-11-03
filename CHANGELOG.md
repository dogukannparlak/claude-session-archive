# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Theme button (follow system / light / dark), remembered per browser; no flash on load.
- Favicon (`favicon.svg`).
- Source icons (official Claude, Obsidian and VS Code logos as SVG, see NOTICE.md) and a source filter: Claude Code app, terminal, Obsidian terminal (heuristic: working
  directory inside a vault), VS Code, SDK.
- `scripts/make_demo_data.py` and `make demo`: synthetic data for screenshots; README screenshots.
- Dates follow the UI language (`en-US` / `tr-TR`) instead of the browser locale.
- `session-archive backup`: copy-only backup of desktop-app sessions (never deletes), so
  Claude Code's age-based cleanup cannot remove them.
- `--projects-dir` can be repeated to browse live and backed-up sessions together.

## [0.1.0] - 2026-11-04

### Added
- Local, read-only web viewer for Claude Code transcripts (`~/.claude/projects/*/*.jsonl`).
- Chat-style rendering: Markdown, code blocks with copy buttons, collapsible tool-call cards
  paired with their results.
- Titles identical to `claude --resume` (`ai-title` / `custom-title` records), with a
  fallback to the first human message.
- Separation of what you typed from what the harness injected (skill bodies, IDE context,
  task notifications, sub-agent reports, compaction summaries): the latter is collapsed
  under a "not written by you" note.
- Full-text search across all sessions, folder filter, branch and file size per session.
- First/last message dates, total span and active time (gaps over 15 minutes are ignored).
- Resizable, collapsible sidebar (drag, double-click to reset, Ctrl/Cmd+B).
- English and Turkish UI (auto-detected, switchable).
- JSON export of a single session and a copy button for the `claude --resume` command.
- Security: loopback-only server, Host-header check (DNS rebinding), strict CSP,
  whitelisted static files, validated session ids.
