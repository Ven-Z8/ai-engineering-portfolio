from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

from second_brain.core.models import RawContent, SourceType


@dataclass
class GitHubRepoAgent:
    max_preview_files: int = 30
    excluded_dir_names: tuple[str, ...] = (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
        ".next",
        ".turbo",
        ".cache",
    )
    excluded_file_names: tuple[str, ...] = (
        ".python-version",
        ".DS_Store",
    )
    excluded_suffixes: tuple[str, ...] = (
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
    )

    def fetch(self, source_url: str) -> RawContent:
        owner, repo = self.parse_owner_repo(source_url)
        with tempfile.TemporaryDirectory(prefix="second-brain-os-github-") as temp_dir:
            checkout_dir = Path(temp_dir) / repo
            self.clone_repo(source_url, checkout_dir)
            return self.fetch_from_checkout(source_url, checkout_dir, owner=owner, repo=repo)

    def fetch_from_checkout(
        self,
        source_url: str,
        checkout_dir: Path,
        *,
        owner: str | None = None,
        repo: str | None = None,
    ) -> RawContent:
        resolved_owner, resolved_repo = self.parse_owner_repo(source_url)
        owner = owner or resolved_owner
        repo = repo or resolved_repo
        readme_content = self.read_readme(checkout_dir)
        structure = self.summarize_structure(checkout_dir)
        parts = []
        if readme_content:
            parts.append("## README\n" + readme_content)
        parts.append("## File Structure Preview\n" + structure)

        return RawContent(
            source_type=SourceType.GITHUB_REPO,
            url=source_url,
            title=f"{owner}/{repo}",
            body="\n\n".join(parts),
            metadata={"owner": owner, "repo": repo, "repo_name": repo},
        )

    def parse_owner_repo(self, source_url: str) -> tuple[str, str]:
        parsed = urlparse(source_url)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Not a GitHub URL: {source_url}")
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise ValueError(f"Could not parse owner/repo from URL: {source_url}")
        return parts[0], parts[1].removesuffix(".git")

    def clone_repo(self, source_url: str, checkout_dir: Path) -> None:
        if shutil.which("git") is None:
            raise RuntimeError("git executable not available in PATH")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", source_url, str(checkout_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr.strip()}")

    def read_readme(self, repo_dir: Path) -> str:
        for candidate in ("README.md", "readme.md", "README.rst", "README.txt"):
            path = repo_dir / candidate
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
        return ""

    def summarize_structure(self, repo_dir: Path) -> str:
        files: list[str] = []
        for path in sorted(repo_dir.rglob("*")):
            if path.is_dir() or self.should_skip_path(path, repo_dir):
                continue
            files.append(f"- `{path.relative_to(repo_dir)}`")
            if len(files) >= self.max_preview_files:
                break
        return "\n".join(files) if files else "No files discovered."

    def should_skip_path(self, path: Path, repo_dir: Path) -> bool:
        relative = path.relative_to(repo_dir)
        if any(part in self.excluded_dir_names for part in relative.parts[:-1]):
            return True
        if path.name in self.excluded_file_names:
            return True
        if path.suffix in self.excluded_suffixes:
            return True
        if path.name.startswith(".") and path.name not in {"README.md", "README.rst", "README.txt"}:
            return True
        return False
