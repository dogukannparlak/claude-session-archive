import json
import tempfile
import unittest
from pathlib import Path

from session_archive.sources import DEFAULT_SOURCES, SourceConfigError, parse_sources, source_of
from session_archive.server import make_server, public_config
from session_archive.store import SessionStore

from .fixtures import OTHER_ID, SESSION_ID, main_session, second_session, write_session

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><rect width="8" height="8"/></svg>'


def rules(items, base=None):
    return parse_sources(items, base)


class RuleMatchingTests(unittest.TestCase):
    def test_first_matching_rule_wins_so_order_is_priority(self):
        r = rules([
            {"key": "work", "match": {"cwd_prefix": ["/srv/work"]}},
            {"key": "term", "match": {"entrypoint": ["cli"]}},
        ])
        self.assertEqual(source_of("cli", "/srv/work/app", r), "work")
        self.assertEqual(source_of("cli", "/home/me", r), "term")
        self.assertEqual(source_of("claude-desktop", "/home/me", r), "other")  # nothing matches -> other

    def test_all_fields_in_a_rule_must_hold_list_items_are_alternatives(self):
        r = rules([{"key": "x", "match": {"entrypoint": ["cli", "sdk-cli"], "cwd_contains": ["/proj/"]}}])
        self.assertEqual(source_of("sdk-cli", "/a/proj/b", r), "x")
        self.assertEqual(source_of("cli", "/a/other/b", r), "other")  # entrypoint ok, path not
        self.assertEqual(source_of("claude-desktop", "/a/proj/b", r), "other")  # path ok, entrypoint not

    def test_cwd_has_walks_up_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "repo" / ".git").mkdir(parents=True)
            (Path(tmp) / "repo" / "src").mkdir()
            r = rules([{"key": "git", "match": {"cwd_has": [".git"]}}])
            self.assertEqual(source_of(None, str(Path(tmp) / "repo" / "src"), r), "git")
            self.assertEqual(source_of(None, tmp, r), "other")

    def test_removing_a_default_source_means_leaving_it_out(self):
        without_obsidian = [d for d in DEFAULT_SOURCES if d["key"] != "obsidian"]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".obsidian").mkdir()
            self.assertEqual(source_of("cli", tmp, rules(DEFAULT_SOURCES)), "obsidian")
            self.assertEqual(source_of("cli", tmp, rules(without_obsidian)), "terminal")

    def test_other_is_always_appended_last(self):
        self.assertEqual([r.key for r in rules([])], ["other"])
        self.assertEqual(rules(DEFAULT_SOURCES)[-1].key, "other")


class ValidationTests(unittest.TestCase):
    def assertRejected(self, items, text):
        with self.assertRaises(SourceConfigError) as ctx:
            rules(items)
        self.assertIn(text, str(ctx.exception))

    def test_errors_are_specific(self):
        ok = {"key": "a", "match": {"entrypoint": ["cli"]}}
        self.assertRejected("nope", "must be a list")
        self.assertRejected([{"match": {"entrypoint": ["cli"]}}], "needs a 'key'")
        self.assertRejected([dict(ok, key="other")], "built-in fallback")
        self.assertRejected([ok, ok], "twice")
        self.assertRejected([dict(ok, icon="no-such-icon")], "unknown icon")
        self.assertRejected([dict(ok, typo=1)], "unknown field")
        self.assertRejected([{"key": "a"}], "non-empty 'match'")
        self.assertRejected([{"key": "a", "match": {"entrypoint_typo": ["cli"]}}], "unknown match field")
        self.assertRejected([{"key": "a", "match": {"entrypoint": "cli ok"}, "icon_file": "missing.svg"}], "icon_file not found")

    def test_icon_file_type_and_size_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.exe").write_bytes(b"x")
            (Path(tmp) / "big.svg").write_bytes(b"x" * (300 * 1024))
            item = {"key": "a", "match": {"entrypoint": ["cli"]}}
            with self.assertRaises(SourceConfigError) as ctx:
                rules([dict(item, icon_file="x.exe")], tmp)
            self.assertIn("icon_file must be one of", str(ctx.exception))
            with self.assertRaises(SourceConfigError) as ctx:
                rules([dict(item, icon_file="big.svg")], tmp)
            self.assertIn("larger than", str(ctx.exception))


class StoreAndServerTests(unittest.TestCase):
    def test_store_uses_custom_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_session(tmp, "-p", SESSION_ID, [dict(r, entrypoint="cli", cwd="/srv/app") for r in main_session()])
            write_session(tmp, "-p", OTHER_ID, second_session())
            r = rules([{"key": "work", "match": {"cwd_prefix": ["/srv"]}}])
            by_id = {s["id"]: s["source"] for s in SessionStore(Path(tmp), sources=r).list_sessions()}
            self.assertEqual(by_id, {SESSION_ID: "work", OTHER_ID: "other"})

    def test_public_config_has_no_filesystem_paths_and_server_serves_custom_icons(self):
        import http.client
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            icon = Path(tmp) / "work.svg"
            icon.write_text(SVG)
            r = rules([{"key": "work", "label": {"en": "Work"}, "icon_file": str(icon), "match": {"cwd_prefix": ["/srv"]}}])
            self.assertNotIn(tmp, json.dumps(public_config(r)))
            server = make_server(SessionStore(Path(tmp), sources=r), 0)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                port = server.server_address[1]

                def get(path):
                    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    c.request("GET", path)
                    res = c.getresponse()
                    body = res.read()
                    c.close()
                    return res, body

                res, body = get("/api/config")
                cfg = json.loads(body)
                self.assertEqual(cfg["sources"][0], {"key": "work", "label": {"en": "Work"}, "icon": {"url": "/icons/user/work.svg"}})
                self.assertEqual(cfg["sources"][-1]["key"], "other")
                res, body = get("/icons/user/work.svg")
                self.assertEqual((res.status, res.getheader("Content-Type")), (200, "image/svg+xml"))
                self.assertEqual(body.decode(), SVG)
                self.assertEqual(get("/icons/user/missing.svg")[0].status, 404)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
