import unittest
from pathlib import Path

from session_archive.store import SessionStore
from session_archive.transcript import build_transcript

from .fixtures import OTHER_ID, SESSION_ID, make_projects_dir


class StoreTests(unittest.TestCase):
    def setUp(self):
        tmp = make_projects_dir()
        self.addCleanup(tmp.cleanup)
        self.store = SessionStore(Path(tmp.name))

    def test_list_is_newest_last_message_first(self):
        ids = [s["id"] for s in self.store.list_sessions()]
        self.assertEqual(ids, [OTHER_ID, SESSION_ID])

    def test_last_ai_title_wins_and_fallback_is_first_human_message(self):
        by_id = {s["id"]: s for s in self.store.list_sessions()}
        self.assertEqual(by_id[SESSION_ID]["title"], "Final title")
        self.assertEqual(by_id[SESSION_ID]["title_src"], "ai")
        self.assertEqual(by_id[OTHER_ID]["title"], "Only a first message, no title records")
        self.assertEqual(by_id[OTHER_ID]["title_src"], "first")

    def test_custom_title_beats_ai_title(self):
        path = self.store.find(SESSION_ID)
        with open(path, "a", encoding="utf-8") as f:
            f.write('{"type": "custom-title", "customTitle": "Renamed"}\n')
        # mtime resolution can be coarse; force the cache to notice the change
        self.store._summary.clear()
        self.assertEqual(self.store.summarize(path)["title"], "Renamed")

    def test_metadata_and_active_time(self):
        s = {x["id"]: x for x in self.store.list_sessions()}[SESSION_ID]
        self.assertEqual(s["cwd"], "/work/demo")
        self.assertEqual(s["branch"], "main")
        self.assertEqual(s["n"], 6)  # sidechain record excluded
        self.assertEqual(s["last"] - s["first"], 3 * 3600 + 150)
        self.assertEqual(s["active"], 150)  # 60 + 5 + 55 + 30 s; the 3 h idle gap is skipped

    def test_find_rejects_bad_ids(self):
        self.assertIsNone(self.store.find("../../etc/passwd"))
        self.assertIsNone(self.store.find("not-a-uuid"))
        self.assertIsNotNone(self.store.find(SESSION_ID))

    def test_search(self):
        hits = self.store.search("needle")
        self.assertEqual([h["id"] for h in hits], [SESSION_ID])
        self.assertIn("needle", hits[0]["snippet"])
        self.assertEqual(self.store.search("x"), [])  # too short
        self.assertEqual(self.store.search("harness noise"), [])  # reminders are not indexed
        self.assertEqual(self.store.search("sidechain"), [])


class TranscriptTests(unittest.TestCase):
    def setUp(self):
        tmp = make_projects_dir()
        self.addCleanup(tmp.cleanup)
        store = SessionStore(Path(tmp.name))
        self.messages = build_transcript(store.find(SESSION_ID))

    def test_kinds_in_order(self):
        kinds = [m["kind"] for m in self.messages]
        self.assertEqual(kinds, ["human", "assistant", "user", "meta", "assistant", "interrupt"])

    def test_reminders_removed_from_user_text(self):
        first = self.messages[0]["parts"][0]["v"]
        self.assertEqual(first, "Hello Claude")

    def test_tool_use_and_result_can_be_paired_by_id(self):
        tool = [p for m in self.messages for p in m["parts"] if p["k"] == "tool"][0]
        result = [p for m in self.messages for p in m["parts"] if p["k"] == "result"][0]
        self.assertEqual(tool["name"], "Bash")
        self.assertEqual(tool["in"], {"command": "ls"})
        self.assertEqual(tool["id"], result["tid"])
        self.assertFalse(result["err"])

    def test_meta_label_is_a_translatable_key(self):
        meta = [m for m in self.messages if m["kind"] == "meta"][0]
        self.assertEqual(meta["label"], "skill_context")


if __name__ == "__main__":
    unittest.main()
