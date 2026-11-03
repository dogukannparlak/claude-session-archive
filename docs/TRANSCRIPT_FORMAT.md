# Transcript format notes

Observed with Claude Code 2.1.x. **This format is unofficial and may change.** Treat every
field as optional.

Each line of `<projects dir>/<project>/<session-id>.jsonl` is one JSON object with a `type`.

## Record types we use

| `type` | Notes |
|---|---|
| `user` | `message.content` is a string or a list of blocks (`text`, `tool_result`, image). Not necessarily written by the person (see below). |
| `assistant` | `message.content` blocks: `text`, `tool_use` (`id`, `name`, `input`), `thinking` (ignored). `message.model` names the model. |
| `ai-title` | `aiTitle`: the generated title shown by `claude --resume`. Appears several times; **the last one wins**. |
| `custom-title` | `customTitle`: set by `/rename`. Overrides `ai-title`. |
| `agent-name` | `agentName`: fallback title. |

Common fields on user/assistant records: `timestamp` (ISO-8601, `Z`), `cwd`, `gitBranch`,
`sessionId`, `isSidechain` (sub-agent records: skipped), `isMeta`, `origin`.

Other types exist (`attachment`, `system`, `last-prompt`, `mode`, `file-history-snapshot`, …) and
are ignored.

## Who wrote a `user` record?

`classify.py` decides, in this order:

1. `origin.kind` is `task-notification`, `peer` or `auto-continuation` → harness (system note).
2. Text starts with `[Request interrupted` → interruption marker.
3. Text starts with `This session is being continued` → compaction summary (system note).
4. `<bash-input>…` → a `!` shell command typed by the user; `<bash-stdout>`/`<local-command…` → output (meta).
5. `<command-name>/x</command-name>` → a slash command typed by the user.
6. `isMeta: true` → skill body or image info (meta).
7. After removing `<system-reminder>` and IDE tags: empty → harness context (meta); otherwise **human**.

When Claude Code changes how it records these, `tests/test_classify.py` is the place to add a
failing example first.

## Tool results

A `tool_result` block lives in a *later* `user` record and refers back via `tool_use_id`. The
frontend pairs them with the `tool_use` by id and hides the result-only records.

## Where a session came from

Records carry `entrypoint`: `cli` (terminal), `claude-desktop` (desktop app Code tab),
`claude-vscode` (VS Code extension), `sdk-cli` (programmatic use). The macOS desktop app also
keeps an index at `~/Library/Application Support/Claude/claude-code-sessions/<account>/<org>/local_*.json`
whose `cliSessionId` is the transcript's file name. `backup.py` uses both to pick app sessions.

Obsidian has no entrypoint of its own: a terminal plugin runs plain `claude`, so those sessions
record `cli`. `sources.py` labels a `cli` session "obsidian" when its `cwd` (or a parent) holds an
`.obsidian` folder. It is a heuristic and checks the filesystem when the summary is built.
