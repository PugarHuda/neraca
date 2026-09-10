"""Vercel entrypoint: NERACA's storefront as a public window into its memory.

A Vercel Function has no durable disk, so this deployment carries a real
snapshot of the bureau's Sibyl store (api/snapshot.db: the demo scenario, the
live Base mainnet ACP scan, the ACP directory) and copies it to /tmp on cold
start. Reads are the real memory as of the commit that built the snapshot;
writes (verdicts, settlements) live only as long as the instance does. The
living bureau - the one that remembers across sessions - runs where its disk
persists: `uvicorn neraca.server:app` on your machine.
"""

import os
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

# The platform's SQLite predates the FTS5 tokenizer Sibyl's store uses: reads
# work, the first write dies with "error in tokenizer constructor". Swap in
# a modern build before anything imports sqlite3.
try:
    import pysqlite3  # noqa: F401
    sys.modules["sqlite3"] = sys.modules["pysqlite3"]
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The Sibyl client keeps a small tier cache under ~/.sibyl-memory; a Function's
# home directory is read-only, /tmp is the only writable disk.
HOME = Path("/tmp/neraca-home")
HOME.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = str(HOME)

SNAPSHOT = ROOT / "api" / "snapshot.db"
LIVE = Path("/tmp/neraca.db")
if SNAPSHOT.exists() and not LIVE.exists():
    shutil.copy(SNAPSHOT, LIVE)
os.environ.setdefault("NERACA_DB", str(LIVE))
os.environ.setdefault(
    "NERACA_DEPLOYMENT_NOTE",
    "Public window: reads come from a real memory snapshot bundled at deploy time; "
    "writes live only as long as this serverless instance. The bureau that remembers "
    "across sessions runs locally (see README).",
)

from neraca.server import app as _app  # noqa: E402  (env must be set before the import)


class _VercelPath:
    """Vercel rewrites every request to /api/index and drops the path, so
    vercel.json tucks it into ?__path=. Hand FastAPI the path the visitor
    actually asked for, and the query string without our marker."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/index"):
            pairs = parse_qsl(scope.get("query_string", b"").decode(), keep_blank_values=True)
            original = "/" + next((v for k, v in pairs if k == "__path"), "").lstrip("/")
            query = urlencode([(k, v) for k, v in pairs if k != "__path"]).encode()
            scope = dict(scope, path=original, raw_path=original.encode(), root_path="", query_string=query)
        try:
            await self.inner(scope, receive, send)
        except Exception:  # make the traceback land in `vercel logs`, then let it fail
            import traceback
            traceback.print_exc()
            raise


app = _VercelPath(_app)
