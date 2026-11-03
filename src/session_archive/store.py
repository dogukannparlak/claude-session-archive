"""Session index: summaries, ordering and full-text search over a projects directory."""
import re

from . import config
from .classify import classify
from .parsing import clean_title, epoch, iter_records, text_of

ID_RE = re.compile(r"^[0-9a-f-]{36}$")


class SessionStore:
    """Read-only view of ``<projects dir>/<project>/<session-id>.jsonl`` files.

    Summaries and the search text are cached per file and invalidated by mtime, so
    only new or changed sessions are re-parsed.
    """

    def __init__(self, root):
        self.root = root
        self._summary = {}  # path -> (mtime, summary dict)
        self._text = {}  # path -> (mtime, lower-cased human + assistant text)

    # -- lookup ---------------------------------------------------------
    def find(self, session_id):
        """Path of a session by id, or ``None``. The id is validated first."""
        if not ID_RE.match(session_id):
            return None
        for path in self.root.glob("*/%s.jsonl" % session_id):
            return path
        return None

    # -- summaries ------------------------------------------------------
    def summarize(self, path):
        st = path.stat()
        hit = self._summary.get(path)
        if hit and hit[0] == st.st_mtime:
            return hit[1]

        custom = ai = agent = first = cwd = branch = None
        count = 0
        t_first = t_last = None
        active = 0.0
        chunks = []

        for rec in iter_records(path):
            rtype = rec.get("type")
            if rtype == "custom-title":  # set by /rename: highest priority
                custom = rec.get("customTitle") or rec.get("title") or custom
            elif rtype == "ai-title":  # the title shown by `claude --resume`; last one wins
                ai = rec.get("aiTitle") or ai
            elif rtype == "agent-name":
                agent = rec.get("agentName") or agent
            elif rtype in ("user", "assistant") and not rec.get("isSidechain"):
                count += 1
                cwd = cwd or rec.get("cwd")
                branch = branch or rec.get("gitBranch")
                ts = epoch(rec.get("timestamp"))
                if ts:
                    if t_last is not None and 0 < ts - t_last <= config.IDLE_SECONDS:
                        active += ts - t_last
                    t_first = t_first if t_first is not None else ts
                    t_last = ts
                content = rec.get("message", {}).get("content")
                if rtype == "user":
                    text = text_of(content)
                    if text.strip():
                        kind, _, body = classify(rec, text)
                        if kind == "human":
                            chunks.append(body)
                            first = first or clean_title(body)
                else:
                    chunks.append(text_of(content))

        self._text[path] = (st.st_mtime, "\n".join(chunks).lower())
        info = {
            "id": path.stem,
            "project": path.parent.name,
            "cwd": cwd or "",
            "branch": branch or "",
            "size": st.st_size,
            "title": (custom or ai or agent or first or "")[:120],
            "title_src": "custom" if custom else "ai" if ai else "agent" if agent else "first",
            "n": count,
            "mtime": st.st_mtime,
            "first": t_first or st.st_mtime,
            "last": t_last or st.st_mtime,
            "active": active,
        }
        self._summary[path] = (st.st_mtime, info)
        return info

    def list_sessions(self):
        """All non-empty sessions, newest *last message* first."""
        items = [self.summarize(p) for p in self.root.glob("*/*.jsonl")]
        items = [i for i in items if i["n"] > 0]
        items.sort(key=lambda i: i["last"], reverse=True)
        return items

    # -- search ---------------------------------------------------------
    def search(self, query):
        """Case-insensitive substring search over human and assistant text."""
        q = query.lower().strip()
        if len(q) < 2:
            return []
        results = []
        for info in self.list_sessions():  # also refreshes the text cache
            path = self.find(info["id"])
            hit = self._text.get(path)
            if not hit:
                continue
            text = hit[1]
            pos = text.find(q)
            if pos < 0:
                continue
            start = max(0, pos - 60)
            snippet = text[start : pos + len(q) + 90].replace("\n", " ")
            results.append({"id": info["id"], "snippet": snippet, "count": text.count(q)})
        return results
