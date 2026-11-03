# Configuration

Everything works with no configuration. When your setup differs (other folders, other tools,
extra sources), change it in one of three places. [Türkçe](CONFIGURATION.tr.md)

| Layer | File | Best for |
|---|---|---|
| Command line | flags such as `--port`, `--projects-dir` | one-off runs |
| Environment | real variables, or a `.env` file (see `.env.example`) | per-machine paths and ports |
| Config file | `session-archive.json` (see `session-archive.example.json`) | paths **and** the list of sources/icons |

Precedence for every setting: **flag > environment > `.env` > config file > default**.

## Where the config file is looked for

First match wins: `--config PATH`, `$SESSION_ARCHIVE_CONFIG`, `./session-archive.json`,
`$XDG_CONFIG_HOME/session-archive/config.json` (`~/.config/...`). The path of the file in use is
printed on start. `.env` is read from the current directory (or `--env-file PATH`).
`session-archive.json` and `.env` are git-ignored; the `*.example` files are tracked.

Generate a complete file with every default written out:

```bash
session-archive print-config > session-archive.json
```

Unknown keys are errors (so typos do not pass silently); keys starting with `_` are ignored, use
them for comments (`"_comment": "..."`). Relative paths are relative to the config file.

## Settings

| Config key | Environment variable | Default | Meaning |
|---|---|---|---|
| `port` | `SESSION_ARCHIVE_PORT` | `8765` | Port on `127.0.0.1` |
| `open_browser` | `SESSION_ARCHIVE_OPEN_BROWSER` | `true` | Open the browser on start |
| `idle_minutes` | `SESSION_ARCHIVE_IDLE_MINUTES` | `15` | Longer gaps do not count as active time |
| `projects_dirs` | `SESSION_ARCHIVE_PROJECTS_DIRS` | `$CLAUDE_CONFIG_DIR/projects` or `~/.claude/projects` | Transcript folders; add a backup folder here |
| `app_index` | `SESSION_ARCHIVE_APP_INDEX` | macOS: `~/Library/Application Support/Claude/claude-code-sessions` | The desktop app's session index (used by `backup`) |
| `backup_dir` | `SESSION_ARCHIVE_BACKUP_DIR` | `~/Documents/claude-session-backup/projects` | Where `session-archive backup` copies to |
| `sources` | (config file only) | the five below | Labels, icons and rules for where a session came from |

Lists in environment variables are separated like `PATH`: `:` on macOS/Linux, `;` on Windows.

### Different paths on your machine

```json
{
  "projects_dirs": ["~/.claude/projects", "/mnt/backup/claude/projects"],
  "app_index": ["~/Library/Application Support/Claude/claude-code-sessions"],
  "backup_dir": "/mnt/backup/claude/projects"
}
```

If you use a custom Claude Code config folder, set `CLAUDE_CONFIG_DIR` (Claude Code's own variable)
and the transcript folder follows it.

## Sources: labels, icons and rules

A *source* says where a session was started and how it is shown. Each session is tested against
the rules **in order; the first match wins**. A session that matches nothing is `other`, a
built-in fallback that always exists (do not define it).

Defaults, so you can see what you are changing:

| key | Icon | Matches |
|---|---|---|
| `desktop` | Claude logo | `entrypoint: claude-desktop` |
| `obsidian` | Obsidian logo | `entrypoint: cli` **and** the working directory is in a folder that has `.obsidian` |
| `terminal` | `>_` | `entrypoint: cli` |
| `vscode` | VS Code logo | `entrypoint: claude-vscode` |
| `sdk` | plug | `entrypoint: sdk-cli`, `sdk-ts`, `sdk-py` |

Because `obsidian` comes before `terminal`, vault sessions win. **Add, remove or reorder** rules
by editing the list: if `sources` is present in your config it *replaces* the defaults, so
a source you leave out disappears. Start from `session-archive print-config`.

A source:

```json
{
  "key": "work",
  "label": {"en": "Work server", "tr": "İş sunucusu"},
  "icon": "server",
  "match": {"cwd_prefix": ["/srv/work", "~/work"]}
}
```

| Field | Meaning |
|---|---|
| `key` | Letters, digits, `-`, `_`. Unique. Not `other`. |
| `label` | Text, or `{language: text}` (the UI picks its language, then English). |
| `icon` | A builtin name (below). |
| `icon_file` | Your own image instead of `icon`: `.svg`, `.png`, `.webp`, `.jpg`, up to 256 KB. Relative to the config file. |
| `match` | At least one field. **All** given fields must hold; list items are alternatives. |

`match` fields:

| Field | True when |
|---|---|
| `entrypoint` | the record's `entrypoint` is one of the listed values (`cli`, `claude-desktop`, `claude-vscode`, `sdk-cli`, ...) |
| `cwd_has` | the working directory **or a parent** contains one of these names (folders or files, e.g. `.obsidian`, `.git`) |
| `cwd_prefix` | the working directory starts with one of these paths (`~` is expanded) |
| `cwd_contains` | the working directory contains one of these substrings |

Builtin icons: `claude`, `obsidian`, `vscode` (product logos, see [NOTICE.md](../NOTICE.md)),
`terminal`, `sdk`, `server`, `folder`, `globe`, `cloud`, `code`, `bolt`, `other` (generic glyphs).

### Examples

Treat everything inside a git repository named `client-x` as its own source, with your own logo:

```json
{"key": "client-x", "label": "Client X", "icon_file": "icons/client-x.svg", "match": {"cwd_contains": ["/client-x/"]}}
```

Keep Obsidian apart from terminals only when started from your vault folder (instead of any folder
with `.obsidian`):

```json
{"key": "obsidian", "icon": "obsidian", "label": "Obsidian", "match": {"entrypoint": ["cli"], "cwd_prefix": ["~/Documents/MyVault"]}}
```

Remove the Obsidian source entirely: delete its entry; those sessions fall to `terminal`.

Notes:
- The Obsidian terminal plugin starts a normal `claude`, so its sessions are only recognisable by
  where they run. That is why rules can look at the working directory.
- Existing folders are checked when a session summary is built, so `cwd_has` costs a few
  filesystem lookups per session (summaries are cached).
- Invalid config stops the start with a message that names the file and the field.
