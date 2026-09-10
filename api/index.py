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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
        await self.inner(scope, receive, send)


app = _VercelPath(_app)
