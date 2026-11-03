import os
import tempfile
import unittest
from pathlib import Path

from session_archive import cli, config
from session_archive.store import SessionStore

from .fixtures import SESSION_ID, isolated_cwd, main_session, write_session

ENV = {"HOME": "/home/x"}  # a controlled "process environment" for load_settings()


def settings_from(dotenv_text="", environ=None, config_json=None):
    """Settings from a throw-away .env text (and optionally a config.json text), in an isolated cwd."""
    with isolated_cwd() as tmp:
        path = Path(tmp) / "test.env"
        path.write_text(dotenv_text or "")
        env = dict(ENV, XDG_CONFIG_HOME=str(Path(tmp) / "xdg"), **(environ or {}))
        cfg = None
        if config_json is not None:
            cfg = Path(tmp) / "cfg.json"
            cfg.write_text(config_json)
        return config.load_settings(path, environ=env, config_path=cfg)


class ParseDotenvTests(unittest.TestCase):
    def test_basic_syntax(self):
        text = """
# a comment
A=1
export B = two
C="quoted # not a comment"
D='single'
E=value # inline comment
EMPTY=
no_equals_sign
=novalue
"""
        self.assertEqual(
            config.parse_dotenv(text),
            {"A": "1", "B": "two", "C": "quoted # not a comment", "D": "single", "E": "value", "EMPTY": ""},
        )

    def test_missing_file_is_empty(self):
        self.assertEqual(config.read_dotenv("/definitely/not/here/.env"), {})


class LoadSettingsTests(unittest.TestCase):
    def test_defaults(self):
        s = settings_from("")
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (8765, True, 900))
        self.assertEqual(s.roots(), [Path.home() / ".claude" / "projects"])
        self.assertIsNone(s.backup_dir)

    def test_dotenv_values(self):
        s = settings_from("SESSION_ARCHIVE_PORT=9000\nSESSION_ARCHIVE_OPEN_BROWSER=off\nSESSION_ARCHIVE_IDLE_MINUTES=5\n")
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (9000, False, 300))

    def test_real_environment_beats_dotenv(self):
        s = settings_from("SESSION_ARCHIVE_PORT=9000\n", {"SESSION_ARCHIVE_PORT": "9100"})
        self.assertEqual(s.port, 9100)

    def test_empty_environment_variable_does_not_override_dotenv(self):
        s = settings_from("SESSION_ARCHIVE_PORT=9000\n", {"SESSION_ARCHIVE_PORT": ""})
        self.assertEqual(s.port, 9000)

    def test_paths_are_split_and_expanded(self):
        raw = os.pathsep.join(["/a/projects", "~/b"])
        s = settings_from("", {"SESSION_ARCHIVE_PROJECTS_DIRS": raw, "SESSION_ARCHIVE_BACKUP_DIR": "~/bak"})
        self.assertEqual(s.roots(), [Path("/a/projects"), Path("~/b").expanduser()])
        self.assertEqual(s.backup_dir, Path("~/bak").expanduser())

    def test_claude_config_dir_sets_the_default_projects_folder(self):
        s = settings_from("", {"CLAUDE_CONFIG_DIR": "/cfg"})
        self.assertEqual(s.roots(), [Path("/cfg/projects")])

    def test_invalid_values_name_the_variable(self):
        for text, name in (
            ("SESSION_ARCHIVE_PORT=abc\n", "SESSION_ARCHIVE_PORT"),
            ("SESSION_ARCHIVE_OPEN_BROWSER=maybe\n", "SESSION_ARCHIVE_OPEN_BROWSER"),
            ("SESSION_ARCHIVE_IDLE_MINUTES=0\n", "SESSION_ARCHIVE_IDLE_MINUTES"),
        ):
            with self.assertRaises(config.ConfigError) as ctx:
                settings_from(text)
            self.assertIn(name, str(ctx.exception))

    def test_repository_example_file_is_valid_and_uses_defaults(self):
        example = Path(__file__).resolve().parent.parent / ".env.example"
        with isolated_cwd():
            s = config.load_settings(example, environ=ENV)
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (8765, True, 900))


class IdleSettingTests(unittest.TestCase):
    def test_idle_threshold_changes_active_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_session(tmp, "-p", SESSION_ID, main_session())
            default = SessionStore(Path(tmp)).list_sessions()[0]["active"]
            wide = SessionStore(Path(tmp), idle_seconds=4 * 3600).list_sessions()[0]["active"]
            self.assertEqual(default, 150)
            self.assertEqual(wide, 3 * 3600 + 150)  # the 3 h gap now counts as active


class CliConfigErrorTests(unittest.TestCase):
    def test_bad_env_file_exits_with_a_clear_message(self):
        with isolated_cwd() as tmp:
            bad = Path(tmp) / "bad.env"
            bad.write_text("SESSION_ARCHIVE_PORT=nope\n")
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--env-file", str(bad), "--projects-dir", tmp])
            self.assertIn("SESSION_ARCHIVE_PORT", str(ctx.exception))

    def test_missing_projects_dir_exits(self):
        with isolated_cwd():
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--projects-dir", "/no/such/dir", "--env-file", "/no/such/.env"])
        self.assertIn("not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
