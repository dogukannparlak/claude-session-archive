"""Command-line entry point: ``session-archive`` (viewer) and ``session-archive backup``.

Precedence for every option: command-line flag > environment variable > ``.env`` file > default
(see ``config.py`` and ``.env.example`` for the setting names).
"""
import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__, backup, config
from .server import make_server
from .store import SessionStore


def _load(args):
    """Settings from ``--env-file`` (or ``./.env``) and the environment; exit with a clear message on errors."""
    try:
        return config.load_settings(args.env_file)
    except config.ConfigError as exc:
        sys.exit("Configuration error: %s" % exc)


def _add_env_file(parser):
    parser.add_argument("--env-file", metavar="PATH", help="settings file (default: ./.env if it exists); see .env.example")


def _backup_main(argv):
    parser = argparse.ArgumentParser(
        prog="session-archive backup",
        description="Copy desktop-app sessions to a safe folder so Claude Code's age-based cleanup cannot delete them. "
        "Only adds or refreshes files; never deletes anything.",
    )
    parser.add_argument("--dest", help="backup folder (setting BACKUP_FOLDER; default: %s)" % backup.default_backup_dir())
    parser.add_argument("--projects-dir", help="transcripts directory to read (default: as for the viewer)")
    parser.add_argument("--app-index", help="desktop app session index (setting APP_INDEX_FOLDER; default: %s)" % backup.default_app_index())
    parser.add_argument("--all", action="store_true", help="back up every session, terminal ones included")
    parser.add_argument("--dry-run", action="store_true", help="show what would be copied, write nothing")
    _add_env_file(parser)
    args = parser.parse_args(argv)
    settings = _load(args)

    src = Path(args.projects_dir).expanduser() if args.projects_dir else settings.roots()[0]
    if not src.is_dir():
        sys.exit("Transcripts directory not found: %s" % src)
    dest = Path(args.dest).expanduser() if args.dest else (settings.backup_dir or backup.default_backup_dir())
    index = [Path(args.app_index).expanduser()] if args.app_index else (settings.app_indexes or backup.default_app_indexes())
    counts = backup.backup(src, dest, index_root=index, include_all=args.all, dry_run=args.dry_run)
    print("%s -> %s%s" % (src, dest, "  (dry run)" if args.dry_run else ""))
    print("selected %(selected)d · new %(copied)d · refreshed %(updated)d · unchanged %(skipped)d" % counts)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "backup":
        return _backup_main(argv[1:])

    parser = argparse.ArgumentParser(
        prog="session-archive",
        description="Browse your local Claude Code session transcripts in the browser (read-only, localhost only).",
    )
    parser.add_argument("--port", type=int, help="port to listen on (setting PORT; default: %d)" % config.DEFAULT_PORT)
    parser.add_argument("--projects-dir", action="append", help="transcript folder; repeat to also read a backup folder "
                        "(setting CLAUDE_FOLDERS; default: $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser (setting OPEN_BROWSER=off)")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    _add_env_file(parser)
    args = parser.parse_args(argv)
    settings = _load(args)

    roots = [Path(p).expanduser() for p in args.projects_dir] if args.projects_dir else settings.roots()
    missing = [r for r in roots if not r.is_dir()]
    if missing:
        sys.exit("Transcripts directory not found: %s\nSet --projects-dir or CLAUDE_FOLDERS in .env." % missing[0])

    port = args.port if args.port is not None else settings.port
    if settings.env_file:
        print("Settings: %s" % settings.env_file)
    for warning in settings.warnings:
        print("Warning: %s" % warning, file=sys.stderr)
    server = make_server(SessionStore(roots, idle_seconds=settings.idle_seconds, sources=settings.sources), port)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("Session Archive: %s  (reading %s, Ctrl+C to stop)" % (url, ", ".join(str(r) for r in roots)))
    if settings.open_browser and not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
