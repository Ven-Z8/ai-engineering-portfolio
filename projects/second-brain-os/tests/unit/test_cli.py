from __future__ import annotations


from typer.testing import CliRunner

from second_brain.cli.main import app
from second_brain.core.models import RawContent, RunStats, SourceType
from second_brain.research.ask import AskResult
from second_brain.vault.index import IndexStats


class FakeRunStats(RunStats):
    def __init__(self) -> None:
        super().__init__()
        self.sources_processed = 1
        self.notes_created = 1


def test_vault_setup_command_creates_scaffold(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "state.db"))
    runner = CliRunner()

    result = runner.invoke(app, ["vault", "setup"])

    assert result.exit_code == 0
    assert "Vault scaffold created at" in result.stdout
    assert (tmp_path / "vault" / "07-Meta" / "MOC-Home.md").exists()


def test_run_command_writes_note_for_single_github_source(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "state.db"))

    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/example/demo",
        title="example/demo",
        body="## README\nDemo repo",
    )

    async def fake_pipeline_run(self, sources, dry_run=False):  # type: ignore[no-untyped-def]
        stats = FakeRunStats()
        note_dir = tmp_path / "vault" / "04-Resources" / "repos"
        note_dir.mkdir(parents=True, exist_ok=True)
        (note_dir / "example-demo.md").write_text("# example/demo\n")
        return stats

    monkeypatch.setattr(
        "second_brain.orchestration.pipeline.Pipeline.run",
        fake_pipeline_run,
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "--source", "github", "--url", raw.url],
    )

    assert result.exit_code == 0
    assert "Done" in result.stdout
    notes = list((tmp_path / "vault" / "04-Resources" / "repos").glob("*.md"))
    assert len(notes) == 1


def test_index_command_reports_index_stats(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "state.db"))

    class FakeVaultIndex:
        @classmethod
        def from_settings(cls, settings):  # type: ignore[no-untyped-def]
            return cls()

        def index(self) -> IndexStats:
            return IndexStats(files_indexed=2, files_skipped=1, chunks_indexed=5)

    monkeypatch.setattr("second_brain.cli.main.VaultIndex", FakeVaultIndex)
    runner = CliRunner()

    result = runner.invoke(app, ["index"])

    assert result.exit_code == 0
    assert "Indexed 2 files" in result.stdout
    assert "5 chunks" in result.stdout
    assert "skipped 1 unchanged" in result.stdout


def test_ask_command_prints_answer_and_sources(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "state.db"))

    class FakeAskService:
        @classmethod
        def from_settings(cls, settings):  # type: ignore[no-untyped-def]
            return cls()

        async def ask(self, question: str, limit: int = 5) -> AskResult:
            assert question == "what is context engineering?"
            assert limit == 5
            return AskResult(
                answer="Use the best evidence within the token budget.",
                sources=["Brain/02-Projects/01-ContextForge/research.md"],
                cost_usd=0.02,
                tokens_used=100,
            )

    monkeypatch.setattr("second_brain.cli.main.AskService", FakeAskService)
    runner = CliRunner()

    result = runner.invoke(app, ["ask", "what is context engineering?"])

    assert result.exit_code == 0
    assert "Use the best evidence" in result.stdout
    assert "Brain/02-Projects/01-ContextForge/research.md" in result.stdout
