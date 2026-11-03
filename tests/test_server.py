import http.client
import json
import threading
import unittest
from pathlib import Path

from session_archive.server import make_server
from session_archive.store import SessionStore

from .fixtures import SESSION_ID, make_projects_dir


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = make_projects_dir()
        cls.server = make_server(SessionStore(Path(cls.tmp.name)), 0)  # port 0: pick a free one
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def get(self, path, host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path, headers={"Host": host or "127.0.0.1:%d" % self.port})
        res = conn.getresponse()
        body = res.read()
        conn.close()
        return res, body

    def test_binds_to_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_static_files_and_security_headers(self):
        for path, ctype in (("/", "text/html"), ("/app.css", "text/css"), ("/js/main.js", "text/javascript")):
            res, body = self.get(path)
            self.assertEqual(res.status, 200, path)
            self.assertTrue(res.getheader("Content-Type").startswith(ctype), path)
            self.assertTrue(body)
        self.assertIn("script-src 'self'", res.getheader("Content-Security-Policy"))
        self.assertEqual(res.getheader("X-Content-Type-Options"), "nosniff")

    def test_foreign_host_header_is_rejected(self):
        res, _ = self.get("/api/sessions", host="evil.example")
        self.assertEqual(res.status, 403)

    def test_sessions_api(self):
        res, body = self.get("/api/sessions")
        self.assertEqual(res.status, 200)
        self.assertEqual(len(json.loads(body)), 2)

    def test_session_detail_and_raw(self):
        res, body = self.get("/api/session/" + SESSION_ID)
        data = json.loads(body)
        self.assertEqual(data["title"], "Final title")
        self.assertTrue(data["messages"])
        res, body = self.get("/api/session/%s?raw=1" % SESSION_ID)
        self.assertIsInstance(json.loads(body), list)

    def test_unknown_and_malicious_paths(self):
        self.assertEqual(self.get("/api/session/not-a-uuid")[0].status, 404)
        self.assertEqual(self.get("/api/session/..%2f..%2fetc%2fpasswd")[0].status, 404)
        self.assertEqual(self.get("/js/../../server.py")[0].status, 404)
        self.assertEqual(self.get("/nope")[0].status, 404)

    def test_search_api(self):
        res, body = self.get("/api/search?q=needle")
        self.assertEqual([h["id"] for h in json.loads(body)], [SESSION_ID])


if __name__ == "__main__":
    unittest.main()
