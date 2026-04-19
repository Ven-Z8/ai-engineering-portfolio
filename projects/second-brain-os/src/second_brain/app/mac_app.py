"""Second Brain OS — Mac desktop app (pywebview + WKWebView).

Run with: sbo-app
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import webview
import yaml

PROJ_DIR = Path(__file__).parent.parent.parent.parent  # app -> second_brain -> src -> second-brain-os/
SOURCES_PATH = PROJ_DIR / "config" / "sources.yaml"
VAULT_PATH = Path("/Volumes/VeN/Claude-Code-Work/Brain")
HTML_PATH = Path(__file__).parent / "static" / "index.html"

_TYPE_TO_KEY = {
    "github": "github_repos",
    "youtube": "youtube",
    "rss": "rss_feeds",
    "web": "web",
}


def _detect_type(url: str) -> str:
    if re.search(r"github\.com/[^/]+/[^/]+", url):
        return "github"
    if re.search(r"(youtube\.com/watch|youtu\.be/)", url):
        return "youtube"
    if re.search(r"\.(rss|atom|xml)(\?|$)", url) or "rss" in url or "feeds" in url:
        return "rss"
    return "web"


def _load_sources() -> dict:
    if SOURCES_PATH.exists():
        return yaml.safe_load(SOURCES_PATH.read_text()) or {}
    return {k: [] for k in _TYPE_TO_KEY.values()}


def _save_sources(sources: dict) -> None:
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text(yaml.dump(sources, default_flow_style=False, allow_unicode=True))


class Api:
    """Python API exposed to JavaScript via window.pywebview.api.*"""

    def add_url(self, url: str, url_type: str) -> dict:
        url = url.strip()
        if not url:
            return {"ok": False, "message": "Empty URL."}
        key = _TYPE_TO_KEY.get(url_type, "web")
        sources = _load_sources()
        sources.setdefault(key, [])
        if url in sources[key]:
            return {"ok": False, "message": f"Already tracked: {url}"}
        sources[key].append(url)
        _save_sources(sources)
        return {"ok": True, "message": f"Added [{url_type}]: {url}"}

    def get_sources(self) -> dict:
        return _load_sources()

    def run_pipeline(self, dry_run: bool = False) -> dict:
        cmd = [str(PROJ_DIR / ".venv" / "bin" / "sbo"), "run"]
        if dry_run:
            cmd.append("--dry-run")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJ_DIR),
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = (result.stdout + result.stderr).strip()
            ok = result.returncode == 0

            # Parse basic stats from Rich table output
            stats = _parse_stats(output)
            return {"ok": ok, "output": output, "stats": stats}
        except subprocess.TimeoutExpired:
            return {"ok": False, "output": "Timeout after 5 minutes.", "stats": None}
        except Exception as exc:
            return {"ok": False, "output": str(exc), "stats": None}

    def run_single(self, url_type: str, url: str) -> dict:
        cmd = [
            str(PROJ_DIR / ".venv" / "bin" / "sbo"),
            "run", "--source", url_type, "--url", url,
        ]
        try:
            result = subprocess.run(
                cmd, cwd=str(PROJ_DIR), capture_output=True, text=True, timeout=180
            )
            output = (result.stdout + result.stderr).strip()
            return {"ok": result.returncode == 0, "output": output}
        except Exception as exc:
            return {"ok": False, "output": str(exc)}

    def search_vault(self, query: str) -> str:
        query = query.strip().lower()
        if not query or not VAULT_PATH.exists():
            return "Vault not found or empty query."

        results: list[str] = []
        for md_file in sorted(VAULT_PATH.rglob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                if query in content.lower():
                    title = md_file.stem
                    for line in content.splitlines()[:6]:
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"')
                            break
                    rel = str(md_file.relative_to(VAULT_PATH))
                    results.append(f"📄 {title}\n   {rel}")
            except Exception:
                pass

        if not results:
            return f"No notes found matching '{query}'."
        header = f"Found {len(results)} note(s) matching '{query}':\n\n"
        return header + "\n\n".join(results[:15]) + (f"\n\n…and {len(results)-15} more" if len(results) > 15 else "")


def _parse_stats(output: str) -> dict | None:
    stats: dict = {}
    patterns = {
        "notes_created": r"Notes created\s*│\s*(\d+)",
        "notes_skipped": r"Notes skipped.*?│\s*(\d+)",
        "cost_usd": r"Cost\s*│\s*\$([0-9.]+)",
        "duration": r"Duration\s*│\s*([\d.]+[ms ]+\d*[s]*)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, output)
        if m:
            val = m.group(1)
            if key in ("notes_created", "notes_skipped"):
                stats[key] = int(val)
            elif key == "cost_usd":
                stats[key] = float(val)
            else:
                stats[key] = val
    return stats or None


def main() -> None:
    api = Api()
    webview.create_window(
        title="Second Brain OS",
        url=str(HTML_PATH),
        js_api=api,
        width=820,
        height=680,
        min_size=(640, 500),
        background_color="#0f0f11",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
