# Contributing

Thanks for helping out! The project is small on purpose: **standard library only on the
backend, plain ES modules on the frontend, no build step.** Please keep it that way.

## Setup

```bash
git clone <your fork>
cd claude-session-archive
make test                # runs the unit tests, no installation needed
make run                 # starts the viewer on http://127.0.0.1:8765
# or install it:
pip install -e .
session-archive --help
```

Requires Python 3.9+. There are no runtime or test dependencies.

## Project layout

```
src/session_archive/
  config.py       settings: .env, environment, flags (friendly errors)
  parsing.py      reading .jsonl, text extraction, timestamps
  classify.py     "did the human write this?" logic
  sources.py      where a session started (icon key)
  transcript.py   one session -> messages for the UI
  store.py        session index, titles, active time, full-text search
  backup.py       copy-only backup of app sessions (never deletes)
  server.py       static files + read-only JSON API (localhost only)
  cli.py          command line
  static/         index.html, app.css, js/*.js (ES modules, i18n in js/i18n.js),
                  icons/ (brand logos, see NOTICE.md), favicon.svg
tests/            unittest suite with synthetic fixtures
scripts/          make_demo_data.py: synthetic sessions for screenshots
docs/             architecture, configuration reference and the transcript format notes
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit.

## Ground rules

1. **Never commit real transcripts**, screenshots of them, or anything from your own
   `~/.claude`. Tests use the synthetic data in `tests/fixtures.py`.
2. **Keep it read-only and local.** The viewer never writes to transcripts (the `backup` command
   only *copies* them and never deletes), no network calls, no
   `--host 0.0.0.0` option. Changes that weaken the guarantees in [SECURITY.md](SECURITY.md)
   will not be merged.
3. **Screenshots use synthetic data only** (`make demo`). Never screenshot your own sessions.
   For sharp (2x) images open `http://127.0.0.1:8770/?lang=en&theme=dark#/<id>`; `?lang=` and
   `?theme=` override the language and theme for that page load only.
4. **Add a test** for backend behaviour changes. Run `make test` and `make lint`.
5. **User-visible text goes through `js/i18n.js`.** Add the key to both `tr` and `en`.
   Backend code returns stable *keys* (e.g. `skill_context`), never display strings.
6. **Escape everything.** Transcript content is untrusted; render it with `esc()` or the
   Markdown renderer, never as raw HTML.
7. Keep commits focused and write messages in the imperative ("Fix idle-time rounding").

## The transcript format is unofficial

Claude Code's `.jsonl` format is not a public API and changes between versions. Parsing
code should be defensive (missing keys, unknown record types) and new assumptions should be
noted in [docs/TRANSCRIPT_FORMAT.md](docs/TRANSCRIPT_FORMAT.md). If you see a record the
viewer misclassifies, open an issue with a **redacted** minimal example of the record.

## Pull requests

- Branch from `main`, keep the diff small, describe the *why*.
- Update `CHANGELOG.md` under "Unreleased".
- CI must pass (Python 3.9 – 3.13).
