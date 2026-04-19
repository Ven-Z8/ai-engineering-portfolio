from __future__ import annotations

import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.table import Table
import typer
import yaml

from second_brain.core.settings import Settings
from second_brain.research.ask import AskService
from second_brain.vault.index import VaultIndex
from second_brain.vault.scaffold import scaffold_vault

app = typer.Typer(help="Second Brain OS — daily knowledge harness")
vault_app = typer.Typer(help="Vault management commands")
add_app = typer.Typer(help="Add sources to sources.yaml")
app.add_typer(vault_app, name="vault")
app.add_typer(add_app, name="add")

console = Console()
SOURCES_PATH = Path("config/sources.yaml")


def load_sources() -> dict[str, list[str]]:
    if SOURCES_PATH.exists():
        return yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    return {"github_repos": [], "youtube": [], "rss_feeds": [], "web": []}


def save_sources(sources: dict[str, list[str]]) -> None:
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text(yaml.dump(sources, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def _build_pipeline(settings: Settings):  # type: ignore[return]
    from second_brain.orchestration.pipeline import Pipeline
    return Pipeline(settings=settings)


@app.command("run")
def run_command(
    source: str | None = typer.Option(None, help="Source type: github, youtube, web, rss"),
    url: str | None = typer.Option(None, help="Single URL to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch but do not write notes"),
) -> None:
    """Run the ingestion pipeline."""
    settings = Settings()
    pipeline = _build_pipeline(settings)

    if source and url:
        source_key = {
            "github": "github_repos",
            "youtube": "youtube",
            "web": "web",
            "rss": "rss_feeds",
        }.get(source)
        if not source_key:
            console.print(f"[red]Unknown source type: {source}[/red]")
            raise typer.Exit(code=1)
        sources = {source_key: [url]}
    else:
        sources = load_sources()

    stats = asyncio.run(pipeline.run(sources=sources, dry_run=dry_run))
    if dry_run:
        console.print("[yellow]Dry run — no notes written[/yellow]")
    else:
        console.print(
            f"[green]Done[/green] — {stats.notes_created} notes created, ${stats.cost_usd:.4f} cost"
        )


@app.command("index")
def index_command() -> None:
    """Index Brain markdown files for semantic vault search."""
    settings = Settings()
    index = VaultIndex.from_settings(settings)
    stats = index.index()
    console.print(
        "[green]Indexed "
        f"{stats.files_indexed} files[/green] "
        f"({stats.chunks_indexed} chunks, skipped {stats.files_skipped} unchanged)"
    )


@app.command("ask")
def ask_command(
    question: str = typer.Argument(..., help="Question to answer from the vault"),
    limit: int = typer.Option(5, "--limit", "-k", help="Number of vault chunks to retrieve"),
) -> None:
    """Ask a vault-first question using semantic search."""
    settings = Settings()
    service = AskService.from_settings(settings)
    result = asyncio.run(service.ask(question, limit=limit))
    console.print(result.answer)
    if result.sources:
        console.print("\n[bold]Sources[/bold]")
        for source in result.sources:
            console.print(f"- {source}")
    if result.cost_usd:
        console.print(f"\n[dim]Cost: ${result.cost_usd:.4f} | Tokens: {result.tokens_used}[/dim]")


@app.command("status")
def status_command() -> None:
    """Show last run stats and vault info."""
    settings = Settings()
    from second_brain.core.db import StateStore
    db = StateStore(db_path=settings.db_path)
    last = db.last_run()
    if not last:
        console.print("[yellow]No runs recorded yet. Run 'sbo run' first.[/yellow]")
        return

    table = Table(title="Last Run")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in last.items():
        table.add_row(str(k), str(v))
    console.print(table)
    console.print(f"\nVault: [cyan]{settings.vault_path}[/cyan]")
    console.print(f"DB:    [cyan]{settings.db_path}[/cyan]")


@vault_app.command("setup")
def vault_setup() -> None:
    """Scaffold vault folder structure."""
    settings = Settings()
    created = scaffold_vault(settings.vault_path)
    console.print(f"[green]Vault scaffold created at {settings.vault_path}[/green]")
    console.print(f"  {len(created)} folders ensured")


@app.command("config")
def config_command() -> None:
    """Open sources.yaml in $EDITOR."""
    editor = os.environ.get("EDITOR", "nano")
    os.system(f"{editor} {SOURCES_PATH}")


@add_app.command("github")
def add_github(url: str = typer.Argument(..., help="GitHub repo URL")) -> None:
    """Add a GitHub repo to sources.yaml."""
    sources = load_sources()
    sources.setdefault("github_repos", [])
    if url not in sources["github_repos"]:
        sources["github_repos"].append(url)
        save_sources(sources)
        console.print(f"[green]Added github:[/green] {url}")
    else:
        console.print(f"[yellow]Already tracked:[/yellow] {url}")


@add_app.command("youtube")
def add_youtube(url: str = typer.Argument(..., help="YouTube video URL")) -> None:
    """Add a YouTube video to sources.yaml."""
    sources = load_sources()
    sources.setdefault("youtube", [])
    if url not in sources["youtube"]:
        sources["youtube"].append(url)
        save_sources(sources)
        console.print(f"[green]Added youtube:[/green] {url}")
    else:
        console.print(f"[yellow]Already tracked:[/yellow] {url}")


@add_app.command("feed")
def add_feed(url: str = typer.Argument(..., help="RSS/Atom feed URL")) -> None:
    """Add an RSS feed to sources.yaml."""
    sources = load_sources()
    sources.setdefault("rss_feeds", [])
    if url not in sources["rss_feeds"]:
        sources["rss_feeds"].append(url)
        save_sources(sources)
        console.print(f"[green]Added feed:[/green] {url}")
    else:
        console.print(f"[yellow]Already tracked:[/yellow] {url}")


@add_app.command("web")
def add_web(url: str = typer.Argument(..., help="Web article URL")) -> None:
    """Add a web URL to sources.yaml."""
    sources = load_sources()
    sources.setdefault("web", [])
    if url not in sources["web"]:
        sources["web"].append(url)
        save_sources(sources)
        console.print(f"[green]Added web:[/green] {url}")
    else:
        console.print(f"[yellow]Already tracked:[/yellow] {url}")
