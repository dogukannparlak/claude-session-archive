"""Settings: defaults < config file (JSON) < ``.env`` file < real environment variables < flags.

Nothing here touches the filesystem at import time. ``load_settings()`` reads an optional
``.env`` file (a tiny parser, no dependency) and the process environment, validates the values
and returns a :class:`Settings`. The command line (see ``cli.py``) overrides it afterwards.

The JSON config file holds the same settings plus the structured ``sources`` list (which
sessions get which label and icon). Where it is looked for, first match wins: ``--config PATH``,
``$SESSION_ARCHIVE_CONFIG``, ``./session-archive.json``, ``$XDG_CONFIG_HOME/session-archive/config.json``
(``~/.config/...``). Keys: ``port``, ``open_browser``, ``idle_minutes``, ``projects_dirs``,
``app_index``, ``backup_dir``, ``sources``. Relative paths are relative to the file.

Variables (all optional):

==================================  =================================================
``SESSION_ARCHIVE_PORT``            port to listen on (default ``8765``)
``SESSION_ARCHIVE_PROJECTS_DIRS``   transcript folders, separated like ``PATH`` (``:`` on
                                    macOS/Linux, ``;`` on Windows). Default: the
                                    ``projects`` folder of ``$CLAUDE_CONFIG_DIR`` or ``~/.claude``
``SESSION_ARCHIVE_OPEN_BROWSER``    ``true``/``false``: open the browser on start (default ``true``)
``SESSION_ARCHIVE_IDLE_MINUTES``    gaps between messages longer than this do not count as
                                    active time (default ``15``)
``SESSION_ARCHIVE_BACKUP_DIR``      destination of ``session-archive backup``
``SESSION_ARCHIVE_APP_INDEX``       the desktop app's session index folder(s), separated like ``PATH``
                                    (macOS default is used if unset)
``SESSION_ARCHIVE_CONFIG``          path of the JSON config file
``CLAUDE_CONFIG_DIR``               Claude Code's own config folder (read, never written)
==================================  =================================================
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .sources import DEFAULT_SOURCES, SourceConfigError, default_rules, parse_sources

DEFAULT_PORT = 8765
DEFAULT_IDLE_MINUTES = 15
IDLE_SECONDS = DEFAULT_IDLE_MINUTES * 60  # kept for callers that need the plain default

# Characters kept per tool input / tool result / message in the transcript API.
MAX_TOOL_INPUT = 3000
MAX_TOOL_RESULT = 4000
MAX_MESSAGE = 6000

TRUE_VALUES = ("1", "true", "yes", "on")
FALSE_VALUES = ("0", "false", "no", "off")


class ConfigError(ValueError):
    """A setting has an invalid value. The message names the variable."""


# -- .env ---------------------------------------------------------------------------------------
def parse_dotenv(text):
    """Parse ``KEY=VALUE`` lines. Supports comments, ``export``, and single/double quotes.

    No variable expansion and no multi-line values. Returns a plain dict.
    """
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
            value = value.split(" #", 1)[0].rstrip()  # inline comment on unquoted values
        values[key] = value
    return values


def read_dotenv(path):
    """Values from a ``.env`` file; ``{}`` if the file does not exist."""
    path = Path(path)
    if not path.is_file():
        return {}
    return parse_dotenv(path.read_text(encoding="utf-8", errors="replace"))


# -- JSON config file ---------------------------------------------------------------------------
JSON_KEYS = ("port", "open_browser", "idle_minutes", "projects_dirs", "app_index", "backup_dir", "sources")


def find_config_file(explicit=None, environ=None):
    """The config file to use, or ``None``. See the module docstring for the search order."""
    environ = os.environ if environ is None else environ
    for candidate in (explicit, environ.get("SESSION_ARCHIVE_CONFIG")):
        if candidate:
            path = Path(candidate).expanduser()
            if not path.is_file():
                raise ConfigError("config file not found: %s" % path)
            return path
    xdg = environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    for path in (Path("session-archive.json"), Path(xdg).expanduser() / "session-archive" / "config.json"):
        if path.is_file():
            return path
    return None


def read_json_config(path):
    """Parse and sanity-check a config file. Unknown keys are errors, so typos do not pass silently."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ConfigError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ConfigError("%s must contain a JSON object" % path)
    unknown = [k for k in data if k not in JSON_KEYS and not k.startswith("_")]  # "_comment" keys are allowed
    if unknown:
        raise ConfigError("%s: unknown key(s) %s (allowed: %s)" % (path, ", ".join(sorted(unknown)), ", ".join(JSON_KEYS)))
    return data


def _json_as_env(data, base_dir):
    """Express JSON settings as environment-style strings so one set of getters validates both."""
    def absolute(value):
        p = Path(value).expanduser()
        return str(p if p.is_absolute() else base_dir / p)

    def paths(value, name):
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError("%s: '%s' must be a list of paths" % ("config file", name))
        return os.pathsep.join(absolute(v) for v in value)

    env = {}
    for key, name, convert in (
        ("port", "SESSION_ARCHIVE_PORT", str),
        ("open_browser", "SESSION_ARCHIVE_OPEN_BROWSER", lambda v: str(v).lower()),
        ("idle_minutes", "SESSION_ARCHIVE_IDLE_MINUTES", str),
        ("projects_dirs", "SESSION_ARCHIVE_PROJECTS_DIRS", lambda v: paths(v, "projects_dirs")),
        ("app_index", "SESSION_ARCHIVE_APP_INDEX", lambda v: paths(v, "app_index")),
        ("backup_dir", "SESSION_ARCHIVE_BACKUP_DIR", lambda v: absolute(v)),
    ):
        if key in data and data[key] is not None:
            env[name] = convert(data[key])
    return env


# -- typed getters ------------------------------------------------------------------------------
def _int(env, name, default, minimum=1):
    raw = env.get(name)
    if raw in (None, ""):
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError("%s must be a whole number, got %r" % (name, raw))
    if value < minimum:
        raise ConfigError("%s must be at least %d, got %d" % (name, minimum, value))
    return value


def _bool(env, name, default):
    raw = env.get(name)
    if raw in (None, ""):
        return default
    low = raw.strip().lower()
    if low in TRUE_VALUES:
        return True
    if low in FALSE_VALUES:
        return False
    raise ConfigError("%s must be true or false, got %r" % (name, raw))


def _path(env, name):
    raw = env.get(name)
    return Path(raw).expanduser() if raw else None


def _paths(env, name):
    raw = env.get(name)
    return [Path(p).expanduser() for p in raw.split(os.pathsep) if p.strip()] if raw else []


def default_projects_dir(env=None):
    """``<config dir>/projects`` where the config dir is ``$CLAUDE_CONFIG_DIR`` or ``~/.claude``."""
    env = os.environ if env is None else env
    base = env.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")
    return Path(base).expanduser() / "projects"


@dataclass
class Settings:
    port: int = DEFAULT_PORT
    projects_dirs: list = field(default_factory=list)  # empty = use default_projects_dir()
    open_browser: bool = True
    idle_seconds: int = IDLE_SECONDS
    backup_dir: Path = None
    app_indexes: list = field(default_factory=list)  # empty = the built-in default(s)
    sources: list = field(default_factory=default_rules)  # SourceRule list, `other` last
    config_file: Path = None  # the JSON file that was used, if any
    default_projects: Path = None  # resolved default, always set by load_settings()

    def roots(self):
        """Transcript folders to read."""
        return self.projects_dirs or [self.default_projects]


def load_settings(dotenv_path=None, environ=None, config_path=None):
    """Build :class:`Settings` from the config file, a ``.env`` file and the environment.

    Precedence: environment > ``.env`` > JSON config > defaults. ``dotenv_path`` defaults to
    ``.env`` in the current directory (ignored if missing). Raises :class:`ConfigError`.
    """
    environ = os.environ if environ is None else environ
    config_file = find_config_file(config_path, environ)
    data, merged = {}, {}
    if config_file:
        data = read_json_config(config_file)
        merged.update(_json_as_env(data, config_file.resolve().parent))
    merged.update(read_dotenv(dotenv_path if dotenv_path is not None else Path(".env")))
    merged.update({k: v for k, v in environ.items() if v != ""})

    try:
        sources = parse_sources(data["sources"], config_file.resolve().parent) if "sources" in data else default_rules()
    except SourceConfigError as exc:
        raise ConfigError("%s: %s" % (config_file, exc))
    return Settings(
        port=_int(merged, "SESSION_ARCHIVE_PORT", DEFAULT_PORT, minimum=0),
        projects_dirs=_paths(merged, "SESSION_ARCHIVE_PROJECTS_DIRS"),
        open_browser=_bool(merged, "SESSION_ARCHIVE_OPEN_BROWSER", True),
        idle_seconds=_int(merged, "SESSION_ARCHIVE_IDLE_MINUTES", DEFAULT_IDLE_MINUTES) * 60,
        backup_dir=_path(merged, "SESSION_ARCHIVE_BACKUP_DIR"),
        app_indexes=_paths(merged, "SESSION_ARCHIVE_APP_INDEX"),
        sources=sources,
        config_file=config_file,
        default_projects=default_projects_dir(merged),
    )


def projects_dir(override=None):
    """Single transcript folder: ``override`` or the default. Kept for simple callers."""
    if override:
        return Path(override).expanduser()
    return default_projects_dir()


def example_config():
    """A complete config file with every default spelled out (``session-archive print-config``)."""
    return {
        "port": DEFAULT_PORT,
        "open_browser": True,
        "idle_minutes": DEFAULT_IDLE_MINUTES,
        "projects_dirs": ["~/.claude/projects"],
        "app_index": ["~/Library/Application Support/Claude/claude-code-sessions"],
        "backup_dir": "~/Documents/claude-session-backup/projects",
        "sources": DEFAULT_SOURCES,
    }
