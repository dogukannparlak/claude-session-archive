import tempfile
import unittest
from pathlib import Path

from session_archive import cli, config
from session_archive.sources import source_of
from session_archive.store import SessionStore

from .fixtures import SESSION_ID, isolated_cwd, main_session, write_session

REPO = Path(__file__).resolve().parent.parent


def load(text="", environ=None, files=()):
    """Settings from a throw-away .env text, in an empty cwd. ``files`` are extra files to create there."""
    with isolated_cwd() as tmp:
        for name in files:
            (Path(tmp) / name).parent.mkdir(parents=True, exist_ok=True)
            (Path(tmp) / name).write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        env_file = Path(tmp) / ".env"
        env_file.write_text(text)
        settings = config.load_settings(env_file, environ=dict(environ or {}))
        settings.tmp = Path(tmp).resolve()
        return settings


class ParseTests(unittest.TestCase):
    def test_basic_syntax(self):
        text = """
# comment
A=1
export B = two
C="quoted # not a comment"
D='single'
E=value # trailing comment
EMPTY=
no_equals
=novalue
"""
        self.assertEqual(
            config.parse_dotenv(text),
            {"A": "1", "B": "two", "C": "quoted # not a comment", "D": "single", "E": "value", "EMPTY": ""},
        )

    def test_missing_file_is_empty(self):
        self.assertEqual(config.read_dotenv("/no/such/.env"), {})


class SimpleValueTests(unittest.TestCase):
    def test_defaults_need_no_file_at_all(self):
        with isolated_cwd():
            s = config.load_settings(environ={})
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (8765, True, 900))
        self.assertEqual(s.roots(), [Path.home() / ".claude" / "projects"])
        self.assertEqual([r.key for r in s.sources], ["desktop", "obsidian", "terminal", "vscode", "sdk", "other"])
        self.assertIsNone(s.env_file)

    def test_numbers_switches_and_words(self):
        s = load("PORT=9000\nOPEN_BROWSER=off\nIDLE_MINUTES=5\n")
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (9000, False, 300))
        for word, expected in (("on", True), ("YES", True), ("true", True), ("1", True), ("Off", False), ("no", False), ("0", False)):
            self.assertIs(load("OPEN_BROWSER=%s\n" % word).open_browser, expected, word)

    def test_prefixed_names_work_in_the_file_and_in_the_environment(self):
        self.assertEqual(load("SESSION_ARCHIVE_PORT=9001\n").port, 9001)
        self.assertEqual(load("", {"SESSION_ARCHIVE_PORT": "9002"}).port, 9002)

    def test_real_environment_beats_the_file_and_plain_PORT_is_ignored(self):
        self.assertEqual(load("PORT=9000\n", {"SESSION_ARCHIVE_PORT": "9100"}).port, 9100)
        self.assertEqual(load("PORT=9000\n", {"PORT": "1234"}).port, 9000)  # other tools' PORT never leaks in

    def test_empty_environment_value_does_not_override_the_file(self):
        self.assertEqual(load("PORT=9000\n", {"SESSION_ARCHIVE_PORT": ""}).port, 9000)

    def test_folders_commas_tilde_and_relative_to_the_env_file(self):
        s = load("CLAUDE_FOLDERS=/a/projects, ~/b , data/c\nBACKUP_FOLDER=~/bak\nAPP_INDEX_FOLDER=idx\n")
        self.assertEqual(s.projects_dirs[:2], [Path("/a/projects"), Path("~/b").expanduser()])
        self.assertEqual(s.projects_dirs[2], s.tmp / "data" / "c")  # relative to the .env file
        self.assertEqual(s.backup_dir, Path("~/bak").expanduser())
        self.assertEqual(s.app_indexes, [s.tmp / "idx"])

    def test_claude_config_dir_moves_the_default_folder(self):
        with isolated_cwd():
            s = config.load_settings(environ={"CLAUDE_CONFIG_DIR": "/cfg"})
        self.assertEqual(s.roots(), [Path("/cfg/projects")])

    def test_unknown_names_only_warn(self):
        s = load("PROT=1\nPORT=9000\n")
        self.assertEqual(s.port, 9000)
        self.assertEqual(len(s.warnings), 1)
        self.assertIn("PROT", s.warnings[0])


class FriendlyErrorTests(unittest.TestCase):
    def assertError(self, text, *words):
        with self.assertRaises(config.ConfigError) as ctx:
            load(text, files=("x.svg",))
        for w in words:
            self.assertIn(w, str(ctx.exception))

    def test_messages_name_the_setting_and_say_what_to_write(self):
        self.assertError("PORT=abc\n", "PORT", "whole number")
        self.assertError("OPEN_BROWSER=maybe\n", "OPEN_BROWSER", "on or off")
        self.assertError("IDLE_MINUTES=0\n", "IDLE_MINUTES", "at least")
        self.assertError("SHOW_VSCODE=sometimes\n", "SHOW_VSCODE", "on or off")
        self.assertError("FOLDER_ICONS=just-a-folder\n", "FOLDER_ICONS", "folder=icon")
        self.assertError("FOLDER_ICONS=~/w=nonsense\n", "FOLDER_ICONS", "not an icon name")
        self.assertError("FOLDER_ICONS=~/w=missing.svg\n", "FOLDER_ICONS", "not found")


class SourceSwitchTests(unittest.TestCase):
    def test_off_removes_the_icon_and_sessions_fall_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".obsidian").mkdir()
            on = load("")
            off = load("SHOW_OBSIDIAN=off\n")
            self.assertEqual(source_of("cli", tmp, on.sources), "obsidian")
            self.assertEqual(source_of("cli", tmp, off.sources), "terminal")  # falls to the next match
            gone = load("SHOW_OBSIDIAN=off\nSHOW_TERMINAL=off\n")
            self.assertEqual(source_of("cli", tmp, gone.sources), "other")

    def test_every_switch_controls_its_source(self):
        for name, key in config.SOURCE_SWITCHES.items():
            self.assertIn(key, [r.key for r in load("").sources])
            self.assertNotIn(key, [r.key for r in load("%s=off\n" % name).sources])


class FolderIconTests(unittest.TestCase):
    def test_builtin_icon_and_own_file_come_first(self):
        s = load("FOLDER_ICONS=/srv/work=server, /home/me/client-x=icons/x.svg\n", files=("icons/x.svg",))
        keys = [r.key for r in s.sources]
        self.assertEqual(keys[:2], ["folder-work", "folder-client-x"])
        self.assertEqual(keys[-1], "other")
        work, client = s.sources[0], s.sources[1]
        self.assertEqual((work.icon, work.label), ("server", "work"))
        self.assertEqual(client.icon_file.resolve(), (s.tmp / "icons" / "x.svg").resolve())
        self.assertEqual(source_of("cli", "/srv/work/app", s.sources), "folder-work")  # beats Terminal
        self.assertEqual(source_of("cli", "/elsewhere", s.sources), "terminal")

    def test_two_folders_with_the_same_name_get_different_keys(self):
        s = load("FOLDER_ICONS=/a/app=server, /b/app=cloud\n")
        self.assertEqual([r.key for r in s.sources[:2]], ["folder-app", "folder-app-2"])


class FilesInTheRepoTests(unittest.TestCase):
    def test_env_example_loads_with_the_defaults(self):
        with isolated_cwd():
            s = config.load_settings(REPO / ".env.example", environ={})
        self.assertEqual((s.port, s.open_browser, s.idle_seconds), (8765, True, 900))
        self.assertEqual(s.warnings, [])

    def test_env_example_documents_every_setting(self):
        text = (REPO / ".env.example").read_text()
        for name in config.KNOWN:
            self.assertIn(name + "=", text, "%s missing from .env.example" % name)


class IdleSettingTests(unittest.TestCase):
    def test_idle_threshold_changes_active_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_session(tmp, "-p", SESSION_ID, main_session())
            self.assertEqual(SessionStore(Path(tmp)).list_sessions()[0]["active"], 150)
            wide = SessionStore(Path(tmp), idle_seconds=4 * 3600).list_sessions()[0]["active"]
            self.assertEqual(wide, 3 * 3600 + 150)  # the 3 h gap now counts as active


class CliTests(unittest.TestCase):
    def test_bad_value_exits_with_a_friendly_message(self):
        with isolated_cwd() as tmp:
            bad = Path(tmp) / "bad.env"
            bad.write_text("PORT=nope\n")
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--env-file", str(bad), "--projects-dir", tmp])
        self.assertIn("PORT", str(ctx.exception))

    def test_missing_projects_dir_exits(self):
        with isolated_cwd():
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--projects-dir", "/no/such/dir", "--env-file", "/no/such/.env"])
        self.assertIn("not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
