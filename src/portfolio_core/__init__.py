"""Shared helpers for every project in this portfolio.

Deliberately small. Anything that only one project needs belongs to that
project, not here -- a shared package that grows by default becomes the thing
nobody dares to change.
"""

from portfolio_core.paths import data_dir, project_root, repo_root
from portfolio_core.seeds import set_seed

__all__ = ["data_dir", "project_root", "repo_root", "set_seed"]
