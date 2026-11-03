import json
import tempfile
import unittest
from pathlib import Path

from session_archive import backup
from session_archive.store import SessionStore

from .fixtures import OTHER_ID, SESSION_ID, main_session, second_session, write_session

THIRD_ID = "99999999-8888-7777-6666-555555555555"


def with_entrypoint(records, entrypoint):
    return [dict(r, entrypoint=entrypoint) for r in records]


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.src, self.dest, self.index = base / "projects", base / "backup", base / "index"
        write_session(self.src, "-p", SESSION_ID, with_entrypoint(main_session(), "claude-desktop"))
        write_session(self.src, "-p", OTHER_ID, with_entrypoint(second_session(), "cli"))
        write_session(self.src, "-p", THIRD_ID, with_entrypoint(second_session(), "cli"))

    def names(self, root):
        return sorted(p.stem for p in Path(root).glob("*/*.jsonl"))

    def test_only_desktop_app_sessions_are_selected_by_default(self):
        counts = backup.backup(self.src, self.dest)
        self.assertEqual(counts, {"selected": 1, "copied": 1, "updated": 0, "skipped": 0})
        self.assertEqual(self.names(self.dest), [SESSION_ID])

    def test_sessions_in_the_app_index_are_selected_too(self):
        self.index.mkdir()
        (self.index / "local_abc.json").write_text(json.dumps({"cliSessionId": OTHER_ID}))
        (self.index / "local_broken.json").write_text("{not json")
        backup.backup(self.src, self.dest, index_root=self.index)
        self.assertEqual(self.names(self.dest), sorted([SESSION_ID, OTHER_ID]))

    def test_all_flag_includes_terminal_sessions(self):
        backup.backup(self.src, self.dest, include_all=True)
        self.assertEqual(self.names(self.dest), sorted([SESSION_ID, OTHER_ID, THIRD_ID]))

    def test_second_run_changes_nothing(self):
        backup.backup(self.src, self.dest)
        counts = backup.backup(self.src, self.dest)
        self.assertEqual((counts["copied"], counts["updated"], counts["skipped"]), (0, 0, 1))

    def test_grown_session_is_refreshed(self):
        backup.backup(self.src, self.dest)
        with open(self.src / "-p" / (SESSION_ID + ".jsonl"), "a") as f:
            f.write(json.dumps({"type": "user", "message": {"content": "more"}}) + "\n")
        counts = backup.backup(self.src, self.dest)
        self.assertEqual(counts["updated"], 1)
        copied = (self.dest / "-p" / (SESSION_ID + ".jsonl")).read_text()
        self.assertIn('"more"', copied)

    def test_never_deletes_or_shrinks_the_backup(self):
        backup.backup(self.src, self.dest)
        (self.src / "-p" / (SESSION_ID + ".jsonl")).unlink()  # simulate Claude Code's cleanup
        counts = backup.backup(self.src, self.dest)
        self.assertEqual(counts["selected"], 0)
        self.assertEqual(self.names(self.dest), [SESSION_ID])  # the backup survives

    def test_dry_run_writes_nothing(self):
        counts = backup.backup(self.src, self.dest, dry_run=True)
        self.assertEqual(counts["copied"], 1)
        self.assertFalse(self.dest.exists())

    def test_no_temp_files_left_behind(self):
        backup.backup(self.src, self.dest, include_all=True)
        self.assertEqual(list(self.dest.rglob("*.tmp")), [])


class MultiRootStoreTests(unittest.TestCase):
    def test_backup_folder_keeps_deleted_sessions_visible_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            live, kept = Path(tmp) / "live", Path(tmp) / "kept"
            write_session(live, "-p", SESSION_ID, main_session())
            write_session(kept, "-p", SESSION_ID, main_session())  # same session in both
            write_session(kept, "-p", OTHER_ID, second_session())  # only in the backup
            store = SessionStore([live, kept])
            self.assertEqual(sorted(s["id"] for s in store.list_sessions()), sorted([SESSION_ID, OTHER_ID]))
            self.assertIsNotNone(store.find(OTHER_ID))


if __name__ == "__main__":
    unittest.main()
