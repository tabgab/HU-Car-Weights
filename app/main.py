"""carWeights FastAPI app: JSON API under /api + /api/v2 + static frontend at /.

The v2 API + /v2/ UI mirror the Android app (Policy Explorer with dynamic
thresholds, filters, detail). The legacy /api + / UI stay intact and can
be toggled between via a top-bar button in either UI.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .routes import router as api_router
from .v2_api import router as v2_router

app = FastAPI(title="carWeights — Hungarian Car Weights & Budapest Parking Fee")
app.include_router(api_router, prefix="/api")
app.include_router(v2_router)  # router already declares prefix="/api/v2"

_WEB = Path(__file__).resolve().parent.parent / "web"


class _UIRedirector:
    """Mount that serves the v2 SPA at /v2/ and the legacy SPA at / (default).

    Implemented as a tiny ASGI wrapper so the existing StaticFiles mounts
    don't fight for the same paths. /v2/ → web/v2/, / → web/.
    """

    def __init__(self, web_root: Path):
        self.web_root = web_root
        self.v2 = StaticFiles(directory=str(web_root / "v2"), html=True)
        self.legacy = StaticFiles(directory=str(web_root), html=True)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.legacy.__call__(scope, receive, send)
            return
        path = scope.get("path", "/")
        # /v2 → /v2/ ; /v2/<...> goes to v2 SPA
        if path == "/v2" or path == "/v2/":
            response = RedirectResponse(url="/v2/index.html")
            await response(scope, receive, send)
            return
        if path.startswith("/v2/"):
            # Strip the /v2 prefix so StaticFiles can serve from web/v2/
            scope = dict(scope)
            scope["path"] = path[3:] or "/"
            await self.v2.__call__(scope, receive, send)
            return
        await self.legacy.__call__(scope, receive, send)


app.mount("/", _UIRedirector(_WEB), name="web")
