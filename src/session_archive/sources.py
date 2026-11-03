"""Where a session was started, and how it is shown (label + icon).

Claude Code records an ``entrypoint`` on every transcript record, and every record carries its
working directory (``cwd``). A *source* is a named rule over those two facts; the first rule that
matches wins, so order is priority. The built-in rules (:data:`DEFAULT_SOURCES`) can be replaced,
extended or trimmed from the config file (see ``config.py``); a session that matches nothing is
``other``, which always exists.

Rule fields (all inside ``match``; every given field must hold, list items are alternatives):

* ``entrypoint``: the record's ``entrypoint`` is one of these (``cli``, ``claude-desktop``, ...)
* ``cwd_has``: the working directory, or one of its parents, contains one of these folder names
* ``cwd_prefix``: the working directory starts with one of these paths
* ``cwd_contains``: the working directory contains one of these substrings

Obsidian is a heuristic: a terminal plugin inside Obsidian starts a plain ``claude`` process, so
its transcript looks exactly like a terminal session. The default rule calls a ``cli`` session
"obsidian" when its working directory is inside a vault (a folder with ``.obsidian``).
"""
import os
from dataclasses import dataclass
from pathlib import Path

# Icons shipped with the app. Files: static/icons/<name>.svg; the rest are inline glyphs.
BUILTIN_ICONS = (
    "claude", "obsidian", "vscode",
    "terminal", "sdk", "server", "folder", "globe", "cloud", "code", "bolt", "other",
)
ICON_FILE_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
MAX_ICON_BYTES = 256 * 1024
OTHER_KEY = "other"

DEFAULT_SOURCES = [
    {"key": "desktop", "label": {"en": "Claude Code app", "tr": "Claude Code uygulaması"}, "icon": "claude",
     "match": {"entrypoint": ["claude-desktop"]}},
    {"key": "obsidian", "label": {"en": "Obsidian terminal", "tr": "Obsidian terminali"}, "icon": "obsidian",
     "match": {"entrypoint": ["cli"], "cwd_has": [".obsidian"]}},
    {"key": "terminal", "label": {"en": "Terminal", "tr": "Terminal"}, "icon": "terminal",
     "match": {"entrypoint": ["cli"]}},
    {"key": "vscode", "label": {"en": "VS Code extension", "tr": "VS Code eklentisi"}, "icon": "vscode",
     "match": {"entrypoint": ["claude-vscode"]}},
    {"key": "sdk", "label": {"en": "SDK / script", "tr": "SDK / betik"}, "icon": "sdk",
     "match": {"entrypoint": ["sdk-cli", "sdk-ts", "sdk-py"]}},
]
OTHER_LABEL = {"en": "Other / unknown", "tr": "Diğer / bilinmiyor"}

MATCH_FIELDS = ("entrypoint", "cwd_has", "cwd_prefix", "cwd_contains")


class SourceConfigError(ValueError):
    """A source definition is invalid. The message says which one and why."""


@dataclass
class SourceRule:
    key: str
    label: object  # str or {lang: str}
    icon: str = "other"  # a builtin icon name ...
    icon_file: Path = None  # ... or a file (svg/png/webp/jpg) of your own
    entrypoint: tuple = ()
    cwd_has: tuple = ()
    cwd_prefix: tuple = ()
    cwd_contains: tuple = ()

    def matches(self, entrypoint, cwd):
        cwd = cwd or ""
        if self.entrypoint and entrypoint not in self.entrypoint:
            return False
        if self.cwd_has and not _has_marker(cwd, self.cwd_has):
            return False
        if self.cwd_prefix and not any(cwd.startswith(os.path.expanduser(p)) for p in self.cwd_prefix):
            return False
        if self.cwd_contains and not any(s in cwd for s in self.cwd_contains):
            return False
        return True


def _has_marker(cwd, names):
    """True if ``cwd`` or a parent holds a folder/file with one of ``names``."""
    if not cwd:
        return False
    path = Path(cwd)
    try:
        return any((d / name).exists() for d in (path, *path.parents) for name in names)
    except OSError:
        return False


def in_obsidian_vault(cwd):
    """True if ``cwd`` or one of its parents contains an ``.obsidian`` folder."""
    return _has_marker(cwd, (".obsidian",))


def _strings(value, where):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise SourceConfigError("%s must be a list of non-empty strings" % where)
    return tuple(value)


def parse_sources(raw, base_dir=None):
    """Validate a list of source definitions (as in the config file) into :class:`SourceRule` s.

    ``base_dir`` resolves relative ``icon_file`` paths (normally the config file's folder).
    The fallback ``other`` source is appended automatically.
    """
    if not isinstance(raw, list):
        raise SourceConfigError("'sources' must be a list")
    rules, seen = [], set()
    for i, item in enumerate(raw):
        where = "sources[%d]" % i
        if not isinstance(item, dict):
            raise SourceConfigError("%s must be an object" % where)
        unknown = set(item) - {"key", "label", "icon", "icon_file", "match"}
        if unknown:
            raise SourceConfigError("%s has unknown field(s): %s" % (where, ", ".join(sorted(unknown))))
        key = item.get("key")
        if not isinstance(key, str) or not key.replace("-", "").replace("_", "").isalnum():
            raise SourceConfigError("%s needs a 'key' of letters, digits, '-' or '_'" % where)
        where = "source %r" % key
        if key == OTHER_KEY:
            raise SourceConfigError("%s: 'other' is the built-in fallback; leave it out" % where)
        if key in seen:
            raise SourceConfigError("%s is defined twice" % where)
        seen.add(key)

        label = item.get("label", key)
        if not (isinstance(label, str) or (isinstance(label, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in label.items()))):
            raise SourceConfigError("%s: 'label' must be text or {language: text}" % where)

        icon, icon_file = item.get("icon", "other"), None
        if item.get("icon_file"):
            icon_file = Path(item["icon_file"]).expanduser()
            if not icon_file.is_absolute() and base_dir:
                icon_file = Path(base_dir) / icon_file
            if icon_file.suffix.lower() not in ICON_FILE_TYPES:
                raise SourceConfigError("%s: icon_file must be one of %s" % (where, ", ".join(sorted(ICON_FILE_TYPES))))
            if not icon_file.is_file():
                raise SourceConfigError("%s: icon_file not found: %s" % (where, icon_file))
            if icon_file.stat().st_size > MAX_ICON_BYTES:
                raise SourceConfigError("%s: icon_file is larger than %d KB" % (where, MAX_ICON_BYTES // 1024))
        elif icon not in BUILTIN_ICONS:
            raise SourceConfigError("%s: unknown icon %r (builtin: %s; or use icon_file)" % (where, icon, ", ".join(BUILTIN_ICONS)))

        match = item.get("match")
        if not isinstance(match, dict) or not match:
            raise SourceConfigError("%s needs a non-empty 'match' object (%s)" % (where, ", ".join(MATCH_FIELDS)))
        bad = set(match) - set(MATCH_FIELDS)
        if bad:
            raise SourceConfigError("%s: unknown match field(s): %s" % (where, ", ".join(sorted(bad))))
        fields = {name: _strings(match[name], "%s match.%s" % (where, name)) for name in match}
        rules.append(SourceRule(key=key, label=label, icon=icon, icon_file=icon_file, **fields))
    rules.append(SourceRule(key=OTHER_KEY, label=OTHER_LABEL, icon="other"))
    return rules


def default_rules():
    return parse_sources(DEFAULT_SOURCES)


DEFAULT_RULES = default_rules()
SOURCES = tuple(r.key for r in DEFAULT_RULES)  # default keys, `other` last


def source_of(entrypoint, cwd=None, rules=None):
    """The key of the first matching rule, else ``other``."""
    for rule in rules or DEFAULT_RULES:
        if rule.key != OTHER_KEY and rule.matches(entrypoint, cwd):
            return rule.key
    return OTHER_KEY
