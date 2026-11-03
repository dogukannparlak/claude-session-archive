"""Command-line entry point: ``session-archive`` (viewer) and ``session-archive backup``."""
import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__, backup, config
from .server import make_server
from .store import SessionStore


def _backup_main(argv):
    parser = argparse.ArgumentParser(
        prog="session-archive backup",
        description="Copy desktop-app sessions to a safe folder so Claude Code's age-based cleanup cannot delete them. "
        "Only adds or refreshes files; never deletes anything.",
    )
    parser.add_argument("--dest", help="backup folder (default: %s)" % backup.default_backup_dir())
    parser.add_argument("--projects-dir", help="transcripts directory to read (default: as for the viewer)")
    parser.add_argument("--app-index", help="desktop app session index (default: %s)" % backup.default_app_index())
    parser.add_argument("--all", action="store_true", help="back up every session, terminal ones included")
    parser.add_argument("--dry-run", action="store_true", help="show what would be copied, write nothing")
    args = parser.parse_args(argv)

    src = config.projects_dir(args.projects_dir)
    if not src.is_dir():
        sys.exit("Transcripts directory not found: %s" % src)
    dest = Path(args.dest).expanduser() if args.dest else backup.default_backup_dir()
    index = Path(args.app_index).expanduser() if args.app_index else backup.default_app_index()
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
    parser.add_argument("--port", type=int, default=config.DEFAULT_PORT, help="port to listen on (default: %(default)s)")
    parser.add_argument("--projects-dir", action="append", help="transcripts directory; repeat to also read a backup folder (default: $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser automatically")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = parser.parse_args(argv)

    roots = [config.projects_dir(p) for p in (args.projects_dir or [None])]
    missing = [r for r in roots if not r.is_dir()]
    if missing:
        sys.exit("Transcripts directory not found: %s\nUse --projects-dir to point at it." % missing[0])

    server = make_server(SessionStore(roots), args.port)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("Session Archive: %s  (reading %s, Ctrl+C to stop)" % (url, ", ".join(str(r) for r in roots)))
    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
