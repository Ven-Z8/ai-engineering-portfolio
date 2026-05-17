"""FastAPI server: serves the HUD HTML and a single /api/skills endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .scanner import scan_skills
from .usage import parse_usage

_PKG_DIR = Path(__file__).resolve().parent
_WEB_DIR = _PKG_DIR.parent / "web"


def create_app() -> FastAPI:
    app = FastAPI(title="Skills HUD", version="0.1.0")

    @app.get("/api/skills")
    def api_skills() -> JSONResponse:
        skills = scan_skills()
        usage = parse_usage()
        rows = []
        unmatched = dict(usage.counts)
        for sk in skills:
            total = 0
            recent = 0
            last: datetime | None = None
            for alias in sk.aliases:
                total += usage.counts.get(alias, 0)
                recent += usage.counts_30d.get(alias, 0)
                lu = usage.last_used.get(alias)
                if lu and (last is None or lu > last):
                    last = lu
                unmatched.pop(alias, None)
            rows.append(
                {
                    "key": sk.key,
                    "name": sk.name,
                    "plugin": sk.plugin,
                    "source": sk.source,
                    "description": sk.description,
                    "total": total,
                    "recent": recent,
                    "last_used": last.isoformat() if last else None,
                    "path": str(sk.path),
                }
            )
        rows.sort(key=lambda r: (-r["recent"], -r["total"], r["key"].lower()))

        return JSONResponse(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sessions_scanned": usage.sessions_scanned,
                "total_skills": len(rows),
                "unmatched_calls": sum(unmatched.values()),
                "skills": rows,
            }
        )

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(_WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")
    return app
