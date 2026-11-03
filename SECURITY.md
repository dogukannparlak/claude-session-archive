# Security policy

## What this tool touches

Session Archive reads the transcripts Claude Code stores on your machine. Those files can
contain source code, secrets pasted into prompts, file contents and personal data, so treat
the viewer's output as sensitive.

Built-in safeguards:

- The server binds to `127.0.0.1` only. There is deliberately no `--host` option.
- Requests whose `Host` header is not `127.0.0.1` or `localhost` are rejected
  (DNS-rebinding protection).
- The API is read-only; the tool never writes to, renames or deletes transcripts. The only
  command that writes is `session-archive backup`, which copies transcripts to a folder you
  choose and never deletes anything.
- Session ids are validated (UUID format) before touching the filesystem, and static files
  are served from a fixed whitelist built at startup.
- A strict Content-Security-Policy is sent (`default-src 'none'`, scripts and styles from
  the same origin only, images from the same origin). Transcript text is HTML-escaped before
  rendering.

## Do not

- Put the server behind a reverse proxy or tunnel on a shared network.
- Leave backups somewhere shared or synced publicly: a backup folder holds the same private
  conversations as `~/.claude`.
- Commit transcripts or exported JSON to a repository (`.gitignore` already excludes
  `*.jsonl`).
- Attach real transcripts to issues. Redact them or use a synthetic example.

## Reporting a vulnerability

Please use GitHub's **private vulnerability reporting** (Security tab → "Report a
vulnerability") instead of opening a public issue. Include the version, steps to reproduce
and the impact. You should get a first response within a week.

Supported versions: only the latest release.
