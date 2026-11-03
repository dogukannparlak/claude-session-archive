"""Command-line entry point: ``session-archive`` / ``python -m session_archive``."""
import argparse
import sys
import threading
import webbrowser

from . import __version__, config
from .server import make_server
from .store import SessionStore


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="session-archive",
        description="Browse your local Claude Code session transcripts in the browser (read-only, localhost only).",
    )
    parser.add_argument("--port", type=int, default=config.DEFAULT_PORT, help="port to listen on (default: %(default)s)")
    parser.add_argument("--projects-dir", help="transcripts directory (default: $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser automatically")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = parser.parse_args(argv)

    root = config.projects_dir(args.projects_dir)
    if not root.is_dir():
        sys.exit("Transcripts directory not found: %s\nUse --projects-dir to point at it." % root)

    server = make_server(SessionStore(root), args.port)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("Session Archive: %s  (reading %s, Ctrl+C to stop)" % (url, root))
    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
