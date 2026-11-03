"""Settings from one simple file: ``.env`` (``NAME=value`` lines).

Order of precedence: command-line flag > real environment variable > ``.env`` file > default.

Values are written the easy way: ``on``/``off`` for switches, a number for numbers, a folder or file
path for paths (``~`` works; several paths are separated by commas). See ``.env.example``.

In the file you write short names (``PORT=8765``). Real environment variables use the same names with
a ``SESSION_ARCHIVE_`` prefix (``SESSION_ARCHIVE_PORT=8765``), so they never clash with other tools.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from .sources import BUILTIN_ICONS, ICON_FILE_TYPES, MAX_ICON_BYTES, SourceConfigError, default_rules, parse_sources

PREFIX = "SESSION_ARCHIVE_"
DEFAULT_PORT = 8765
DEFAULT_IDLE_MINUTES = 15
IDLE_SECONDS = DEFAULT_IDLE_MINUTES * 60  # the default, for callers that need the plain number

# Characters kept per tool input / tool result / message in the transcript API.
MAX_TOOL_INPUT = 3000
MAX_TOOL_RESULT = 4000
MAX_MESSAGE = 6000

# Switches that show or hide a built-in source icon. Off = no separate icon: the session falls
# through to the next matching source (e.g. Obsidian off -> Terminal).
SOURCE_SWITCHES = {
    "SHOW_APP": "desktop",
    "SHOW_OBSIDIAN": "obsidian",
    "SHOW_TERMINAL": "terminal",
    "SHOW_VSCODE": "vscode",
    "SHOW_SDK": "sdk",
}
NUMBERS = ("PORT", "IDLE_MINUTES")
SWITCHES = ("OPEN_BROWSER",) + tuple(SOURCE_SWITCHES)
PATHS = ("CLAUDE_FOLDERS", "BACKUP_FOLDER", "APP_INDEX_FOLDER", "FOLDER_ICONS")
KNOWN = NUMBERS + SWITCHES + PATHS

TRUE_WORDS = ("on", "yes", "true", "1")
FALSE_WORDS = ("off", "no", "false", "0")


class ConfigError(ValueError):
    """A setting has an invalid value. The message names the setting and says what to write."""


# -- reading the file ----------------------------------------------------------------------------
def parse_dotenv(text):
    """Parse ``NAME=value`` lines (comments with ``#``, optional quotes and ``export``). Returns a dict."""
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()  # a trailing "# comment"
        values[key] = value
    return values


def read_dotenv(path):
    """Values from a ``.env`` file; ``{}`` if it does not exist."""
    path = Path(path)
    if not path.is_file():
        return {}
    return parse_dotenv(path.read_text(encoding="utf-8", errors="replace"))


def _short(name):
    """``SESSION_ARCHIVE_PORT`` and ``PORT`` are the same setting."""
    name = name.strip().upper()
    return name[len(PREFIX):] if name.startswith(PREFIX) else name


# -- typed getters -------------------------------------------------------------------------------
def _number(values, name, default, minimum):
    raw = values.get(name)
    if raw in (None, ""):
        return default
    try:
        number = int(raw)
    except ValueError:
        raise ConfigError("%s: write a whole number, for example %s=%d (you wrote %r)" % (name, name, default, raw))
    if number < minimum:
        raise ConfigError("%s: must be at least %d (you wrote %d)" % (name, minimum, number))
    return number


def _switch(values, name, default=True):
    raw = values.get(name)
    if raw in (None, ""):
        return default
    word = raw.strip().lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ConfigError("%s: write on or off (you wrote %r)" % (name, raw))


def _list(raw):
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else []


def _paths(values, name, base):
    """Comma-separated paths -> absolute-ish ``Path`` list. ``~`` expands; relative = relative to ``base``."""
    out = []
    for item in _list(values.get(name)):
        path = Path(item).expanduser()
        out.append(path if path.is_absolute() or base is None else base / path)
    return out


def default_projects_dir(environ=None):
    """``<config dir>/projects`` where the config dir is ``$CLAUDE_CONFIG_DIR`` or ``~/.claude``."""
    environ = os.environ if environ is None else environ
    base = environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")
    return Path(base).expanduser() / "projects"


# -- FOLDER_ICONS ----------------------------------------------------------------------------------
def _folder_rules(raw, base):
    """``FOLDER_ICONS=~/work=server, ~/client-x=./x.svg`` -> source rules (checked before the defaults).

    Each item is ``folder=icon`` where icon is a built-in icon name or the path of your own image.
    """
    items, used = [], set()
    for entry in _list(raw):
        folder, sep, icon = entry.rpartition("=")
        folder, icon = folder.strip(), icon.strip()
        if not sep or not folder or not icon:
            raise ConfigError("FOLDER_ICONS: write folder=icon, for example ~/work=server (you wrote %r)" % entry)
        name = Path(folder).expanduser().name or "folder"
        slug = "folder-" + "".join(c if c.isalnum() else "-" for c in name.lower())
        key, n = slug, 2
        while key in used:  # two folders with the same name get -2, -3, ...
            key, n = "%s-%d" % (slug, n), n + 1
        used.add(key)
        item = {"key": key, "label": name, "match": {"cwd_prefix": [str(Path(folder).expanduser())]}}
        if icon in BUILTIN_ICONS:
            item["icon"] = icon
        else:
            path = Path(icon).expanduser()
            path = path if path.is_absolute() or base is None else base / path
            if path.suffix.lower() not in ICON_FILE_TYPES:
                raise ConfigError("FOLDER_ICONS: %r is not an icon name. Use one of: %s, or the path of an "
                                  ".svg/.png/.webp/.jpg file" % (icon, ", ".join(BUILTIN_ICONS)))
            if not path.is_file():
                raise ConfigError("FOLDER_ICONS: icon file not found: %s" % path)
            if path.stat().st_size > MAX_ICON_BYTES:
                raise ConfigError("FOLDER_ICONS: icon file is too large (max %d KB): %s" % (MAX_ICON_BYTES // 1024, path))
            item["icon_file"] = str(path)
        items.append(item)
    try:
        return parse_sources(items)[:-1]  # drop the automatic "other"; it is added once at the end
    except SourceConfigError as exc:
        raise ConfigError("FOLDER_ICONS: %s" % exc)


@dataclass
class Settings:
    port: int = DEFAULT_PORT
    projects_dirs: list = field(default_factory=list)  # empty = use default_projects
    open_browser: bool = True
    idle_seconds: int = IDLE_SECONDS
    backup_dir: Path = None
    app_indexes: list = field(default_factory=list)  # empty = the built-in default
    sources: list = field(default_factory=default_rules)  # SourceRule list, `other` last
    env_file: Path = None  # the .env that was read, if any
    warnings: list = field(default_factory=list)  # e.g. unknown names in the file
    default_projects: Path = None

    def roots(self):
        """Transcript folders to read."""
        return self.projects_dirs or [self.default_projects]


def load_settings(dotenv_path=None, environ=None):
    """Build :class:`Settings` from ``.env`` (default: ``./.env`` if present) and the environment.

    Raises :class:`ConfigError` with a message that names the setting and says what to write.
    """
    environ = os.environ if environ is None else environ
    path = Path(dotenv_path) if dotenv_path is not None else Path(".env")
    from_file = {_short(k): v for k, v in read_dotenv(path).items()}
    base = path.resolve().parent if path.is_file() else None

    warnings = ["%s: unknown setting %s (ignored)" % (path.name, k) for k in from_file if k not in KNOWN]
    values = dict(from_file)
    for key, value in environ.items():  # real environment: only the prefixed names, so PORT etc. never clash
        if key.upper().startswith(PREFIX) and value != "" and _short(key) in KNOWN:
            values[_short(key)] = value

    hidden = {key for name, key in SOURCE_SWITCHES.items() if not _switch(values, name)}
    sources = _folder_rules(values.get("FOLDER_ICONS"), base) + [r for r in default_rules() if r.key not in hidden]

    return Settings(
        port=_number(values, "PORT", DEFAULT_PORT, 0),
        projects_dirs=_paths(values, "CLAUDE_FOLDERS", base),
        open_browser=_switch(values, "OPEN_BROWSER"),
        idle_seconds=_number(values, "IDLE_MINUTES", DEFAULT_IDLE_MINUTES, 1) * 60,
        backup_dir=(_paths(values, "BACKUP_FOLDER", base) or [None])[0],
        app_indexes=_paths(values, "APP_INDEX_FOLDER", base),
        sources=sources,
        env_file=path if path.is_file() else None,
        warnings=warnings,
        default_projects=default_projects_dir(environ),
    )


def projects_dir(override=None):
    """Single transcript folder: ``override`` or the default. Kept for simple callers."""
    if override:
        return Path(override).expanduser()
    return default_projects_dir()
