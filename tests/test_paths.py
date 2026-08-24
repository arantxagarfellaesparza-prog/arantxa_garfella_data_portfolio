"""These tests exist because path bugs are silent: the wrong directory is
created, the write succeeds, and the mistake only surfaces when a result cannot
be reproduced."""

from pathlib import Path

import pytest

from portfolio_core.paths import data_dir, project_root, repo_root


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "projects" / "01-demo" / "notebooks").mkdir(parents=True)
    return tmp_path


def test_repo_root_is_the_directory_holding_pyproject(fake_repo: Path) -> None:
    deep = fake_repo / "projects" / "01-demo" / "notebooks"
    assert repo_root(deep) == fake_repo


def test_repo_root_raises_outside_a_repository(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        repo_root(tmp_path)


def test_project_root_stops_at_the_project_not_the_repo(fake_repo: Path) -> None:
    deep = fake_repo / "projects" / "01-demo" / "notebooks"
    assert project_root(deep) == fake_repo / "projects" / "01-demo"


def test_project_root_refuses_to_fall_back_to_the_repo(fake_repo: Path) -> None:
    # Called from outside any project it must fail, not quietly return the repo:
    # a silent fallback would put a project's data in the shared root.
    with pytest.raises(FileNotFoundError):
        project_root(fake_repo)


def test_data_dir_creates_the_folder(fake_repo: Path) -> None:
    origin = fake_repo / "projects" / "01-demo" / "notebooks"
    created = data_dir("processed", start=origin)
    assert created == fake_repo / "projects" / "01-demo" / "data" / "processed"
    assert created.is_dir()


def test_data_dir_rejects_an_unknown_kind(fake_repo: Path) -> None:
    origin = fake_repo / "projects" / "01-demo" / "notebooks"
    with pytest.raises(ValueError, match="raw"):
        data_dir("final", start=origin)
