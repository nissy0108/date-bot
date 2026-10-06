"""Static assets with no-cache for JS/CSS during local dev."""

from __future__ import annotations

from fastapi.staticfiles import StaticFiles
from starlette.responses import Response


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        if path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response
