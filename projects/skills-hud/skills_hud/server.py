"""FastAPI server: serves the HUD HTML and a single /api/skills endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .scanner import scan_skills
from .usage import SOURCES, parse_usage

_PKG_DIR = Path(__file__).resolve().parent
_WEB_DIR = _PKG_DIR.parent / "web"


def create_app() -> FastAPI:
    app = FastAPI(title="Skills HUD", version="0.2.0")

    @app.get("/api/skills")
    def api_skills() -> JSONResponse:
        skills = scan_skills()
        usage = parse_usage()
        rows = []
        unmatched: dict[str, dict[str, int]] = {}
        # Track which raw skill strings have been claimed by an installed skill.
        claimed: set[str] = set()

        for sk in skills:
            breakdown = {s: 0 for s in SOURCES}
            breakdown_30d = {s: 0 for s in SOURCES}
            last: datetime | None = None
            for alias in sk.aliases:
                for source, n in usage.by_source.get(alias, {}).items():
                    breakdown[source] += n
                for source, n in usage.by_source_30d.get(alias, {}).items():
                    breakdown_30d[source] += n
                lu = usage.last_used.get(alias)
                if lu and (last is None or lu > last):
                    last = lu
                if alias in usage.by_source:
                    claimed.add(alias)
            total = sum(breakdown.values())
            recent = sum(breakdown_30d.values())
            rows.append(
                {
                    "key": sk.key,
                    "name": sk.name,
                    "plugin": sk.plugin,
                    "source": sk.source,
                    "description": sk.description,
                    "kind": sk.kind,
                    "total": total,
                    "recent": recent,
                    "breakdown": breakdown,
                    "breakdown_30d": breakdown_30d,
                    "last_used": last.isoformat() if last else None,
                    "path": str(sk.path),
                }
            )
        rows.sort(key=lambda r: (-r["recent"], -r["total"], r["key"].lower()))

        # Surface any skill strings we saw in logs but couldn't match to an installed skill —
        # e.g. built-in CLI commands like /plugin, /login, or skills that got uninstalled.
        for skill_str, by_src in usage.by_source.items():
            if skill_str in claimed:
                continue
            unmatched[skill_str] = dict(by_src)

        return JSONResponse(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sessions_scanned": usage.sessions_scanned,
                "total_skills": len(rows),
                "unmatched": unmatched,
                "unmatched_count": sum(sum(v.values()) for v in unmatched.values()),
                "skills": rows,
            }
        )

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(_WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")
    return app
