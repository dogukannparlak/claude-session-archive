"""Tiny HTTP layer: static files + a read-only JSON API. Bound to localhost only."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .parsing import iter_records
from .transcript import build_transcript

STATIC_DIR = Path(__file__).with_name("static")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _static_routes():
    """Map URL path -> (file, content type) for every html/css/js/svg file under static/.

    Built once from a directory scan, so a request can only ever reach a file that
    exists in this table (no path traversal possible).
    """
    routes = {}
    for path in STATIC_DIR.rglob("*"):
        if path.suffix in CONTENT_TYPES and path.is_file():
            url = "/" + path.relative_to(STATIC_DIR).as_posix()
            routes[url] = (path, CONTENT_TYPES[path.suffix])
    routes["/"] = routes.pop("/index.html")
    return routes


STATIC_ROUTES = _static_routes()

ALLOWED_HOSTS = ("127.0.0.1", "localhost")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
}


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal quiet
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            for key, value in SECURITY_HEADERS.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, payload, code=200):
            self._send(code, json.dumps(payload, ensure_ascii=False))

        def do_GET(self):
            # DNS-rebinding protection: only answer requests addressed to localhost.
            host = (self.headers.get("Host") or "").split(":")[0]
            if host not in ALLOWED_HOSTS:
                return self._send(403, "forbidden", "text/plain")

            url = urlparse(self.path)
            query = parse_qs(url.query)

            if url.path in STATIC_ROUTES:
                file, ctype = STATIC_ROUTES[url.path]
                return self._send(200, file.read_bytes(), ctype)
            if url.path == "/api/sessions":
                return self._json(store.list_sessions())
            if url.path == "/api/search":
                return self._json(store.search(query.get("q", [""])[0]))
            if url.path.startswith("/api/session/"):
                path = store.find(url.path.rsplit("/", 1)[1])
                if not path:
                    return self._json({"error": "not found"}, 404)
                if query.get("raw"):
                    body = json.dumps(list(iter_records(path)), ensure_ascii=False, indent=1)
                    return self._send(200, body)
                info = store.summarize(path)
                return self._json({**info, "messages": build_transcript(path)})
            self._send(404, "not found", "text/plain")

    return Handler


def make_server(store, port):
    """Create (but do not start) a server bound to 127.0.0.1 only."""
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
