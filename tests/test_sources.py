import tempfile
import unittest
from pathlib import Path

from session_archive.sources import SOURCES, source_of
from session_archive.store import SessionStore

from .fixtures import OTHER_ID, SESSION_ID, main_session, second_session, write_session


class SourceTests(unittest.TestCase):
    def test_known_entrypoints(self):
        self.assertEqual(source_of("cli"), "terminal")
        self.assertEqual(source_of("claude-desktop"), "desktop")
        self.assertEqual(source_of("claude-vscode"), "vscode")
        self.assertEqual(source_of("sdk-cli"), "sdk")
        self.assertEqual(source_of("sdk-ts"), "sdk")

    def test_unknown_or_missing_entrypoint_falls_back_to_other(self):
        self.assertEqual(source_of(None), "other")
        self.assertEqual(source_of("some-future-client"), "other")
        self.assertIn(source_of("whatever"), SOURCES)

    def test_cli_session_inside_an_obsidian_vault_is_obsidian(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "notes"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "sub").mkdir()
            self.assertEqual(source_of("cli", str(vault)), "obsidian")
            self.assertEqual(source_of("cli", str(vault / "sub")), "obsidian")  # parent has .obsidian
            self.assertEqual(source_of("cli", tmp), "terminal")
            self.assertEqual(source_of("claude-desktop", str(vault)), "desktop")  # only terminals are reclassified
            self.assertEqual(source_of("cli", "/does/not/exist"), "terminal")
            self.assertEqual(source_of("cli", None), "terminal")

    def test_store_reports_source_per_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_session(tmp, "-p", SESSION_ID, [dict(r, entrypoint="claude-desktop") for r in main_session()])
            write_session(tmp, "-p", OTHER_ID, second_session())  # no entrypoint recorded
            by_id = {s["id"]: s for s in SessionStore(Path(tmp)).list_sessions()}
            self.assertEqual((by_id[SESSION_ID]["source"], by_id[SESSION_ID]["entrypoint"]), ("desktop", "claude-desktop"))
            self.assertEqual((by_id[OTHER_ID]["source"], by_id[OTHER_ID]["entrypoint"]), ("other", ""))


if __name__ == "__main__":
    unittest.main()
