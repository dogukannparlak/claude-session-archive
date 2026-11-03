# Configuration

One small file: **`.env`**. Copy the example and change what you need. Nothing is required.

```bash
cp .env.example .env
```

Write values the easy way: `on` / `off`, a number, or a folder/file path (`~` works; several paths
are separated by commas). Delete a line to get the default. [Türkçe](CONFIGURATION.tr.md)

| Setting | You write | Default | What it does |
|---|---|---|---|
| `PORT` | a number | `8765` | The viewer opens at `http://127.0.0.1:PORT` |
| `OPEN_BROWSER` | `on` / `off` | `on` | Open the browser when it starts |
| `IDLE_MINUTES` | a number | `15` | Gaps longer than this do not count as work time |
| `CLAUDE_FOLDERS` | folder(s) | `~/.claude/projects` | Where your Claude Code conversations are. Add a backup folder after a comma |
| `BACKUP_FOLDER` | a folder | `~/Documents/claude-session-backup/projects` | Where `session-archive backup` puts its copies |
| `APP_INDEX_FOLDER` | a folder | macOS location (built in) | The Claude desktop app's session list |
| `SHOW_APP` | `on` / `off` | `on` | Icon for the Claude Code app |
| `SHOW_OBSIDIAN` | `on` / `off` | `on` | Icon for terminals started inside an Obsidian vault |
| `SHOW_TERMINAL` | `on` / `off` | `on` | Icon for normal terminals |
| `SHOW_VSCODE` | `on` / `off` | `on` | Icon for VS Code |
| `SHOW_SDK` | `on` / `off` | `on` | Icon for scripts / SDK |
| `FOLDER_ICONS` | `folder=icon`, ... | none | Your own icon for a folder (below) |

`off` means that source gets no icon of its own: with `SHOW_OBSIDIAN=off`, vault sessions show as
Terminal. Relative paths are relative to the `.env` file.

## Examples

```ini
# other port, do not open the browser
PORT=9000
OPEN_BROWSER=off

# read a second folder (a backup) as well
CLAUDE_FOLDERS=~/.claude/projects, ~/Documents/claude-backup/projects

# I do not use VS Code or Obsidian: hide those icons
SHOW_VSCODE=off
SHOW_OBSIDIAN=off

# sessions started under ~/work get the "server" icon, ~/client-x gets my own logo
FOLDER_ICONS=~/work=server, ~/Documents/client-x=./icons/client-x.svg
```

`FOLDER_ICONS` takes `folder=icon` pairs. The icon is a name (`server`, `folder`, `globe`, `cloud`,
`code`, `bolt`) or the path of your own `.svg` / `.png` / `.webp` / `.jpg` file, up to 256 KB. The
label shown is the folder's name. Folder icons win over the built-in ones.

## Other ways

* **Command line** overrides the file: `session-archive --port 9000 --no-open --projects-dir ~/x`.
* **Environment variables** use the same names with a `SESSION_ARCHIVE_` prefix
  (`SESSION_ARCHIVE_PORT=9000`), so they never clash with other tools' `PORT`.
* `--env-file PATH` reads another file. A custom Claude Code config folder is picked up from
  `CLAUDE_CONFIG_DIR` (Claude Code's own variable).

Order of precedence: command line > environment > `.env` > default.

A mistake in the file stops the start with a message that says which setting and what to write
(`PORT: write a whole number...`). A name that does not exist only prints a warning.
