"""Locate files by walking up from the caller, never by relative path.

A notebook opened from `notebooks/` and a script run from the repo root have
different working directories, so `pd.read_csv("data/raw/events.csv")` works in
one and fails in the other. Resolving from an anchor file removes the ambiguity:
the answer no longer depends on where the process was started.
"""

from __future__ import annotations

from pathlib import Path

# `.git` is not in the list: it is absent in a shallow copy, a zip download or a
# git worktree, so it is not a reliable marker of the repo root.
_REPO_MARKERS = ("pyproject.toml",)
_PROJECT_MARKERS = ("project.toml", "README.md")


def _find_upwards(
    start: Path, markers: tuple[str, ...], *, stop: Path | None = None
) -> Path | None:
    """Return the closest ancestor of `start` containing any of `markers`."""
    current = start if start.is_dir() else start.parent
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in markers):
            return candidate
        if stop is not None and candidate == stop:
            break
    return None


def repo_root(start: Path | str | None = None) -> Path:
    """Absolute path of the repository root (the directory holding pyproject.toml)."""
    origin = Path(start).resolve() if start is not None else Path(__file__).resolve()
    found = _find_upwards(origin, _REPO_MARKERS)
    if found is None:
        raise FileNotFoundError(
            f"No pyproject.toml found in any parent of {origin}. "
            "Is this file inside the portfolio repository?"
        )
    return found


def project_root(start: Path | str | None = None) -> Path:
    """Absolute path of the individual project (e.g. projects/01-product-analytics).

    Called from inside a project, returns that project's directory. The search
    stops at the repo root so a stray call from shared code fails loudly instead
    of silently returning the repo itself and writing data in the wrong place.
    """
    origin = Path(start).resolve() if start is not None else Path.cwd()
    root = repo_root(origin if origin.is_dir() else origin.parent)
    projects = root / "projects"

    current = origin if origin.is_dir() else origin.parent
    for candidate in (current, *current.parents):
        if candidate == projects or candidate == root:
            break
        if candidate.parent == projects:
            return candidate

    raise FileNotFoundError(
        f"{origin} is not inside a project under {projects}. "
        "project_root() is only meaningful from within projects/<name>/."
    )


def data_dir(kind: str = "raw", start: Path | str | None = None) -> Path:
    """Path to a project's data folder, creating it if needed.

    `raw` is downloaded or generated and never edited by hand; `interim` holds
    intermediate steps; `processed` is what analysis and models read. Keeping
    them apart is what makes "re-run everything from scratch" a real option.
    """
    allowed = {"raw", "interim", "processed"}
    if kind not in allowed:
        raise ValueError(f"kind must be one of {sorted(allowed)}, got {kind!r}")

    target = project_root(start) / "data" / kind
    target.mkdir(parents=True, exist_ok=True)
    return target
