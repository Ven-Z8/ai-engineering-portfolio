from __future__ import annotations

from pathlib import Path

from second_brain.vault.scaffold import scaffold_vault, PROJECT_FOLDERS


def test_scaffold_vault_creates_core_directories_and_files(tmp_path: Path) -> None:
    scaffold_vault(tmp_path)

    assert (tmp_path / "00-Inbox").is_dir()
    assert (tmp_path / "01-Daily" / "templates").is_dir()
    assert (tmp_path / "04-Resources" / "repos").is_dir()
    assert (tmp_path / "07-Meta").is_dir()
    assert (tmp_path / "07-Meta" / "MOC-Home.md").exists()
    assert (tmp_path / "02-Projects" / "00-Portfolio-Overview.md").exists()


def test_scaffold_vault_creates_all_24_project_folders(tmp_path: Path) -> None:
    scaffold_vault(tmp_path)

    created = sorted(
        path.name
        for path in (tmp_path / "02-Projects").iterdir()
        if path.is_dir()
    )

    assert created == sorted(PROJECT_FOLDERS)
