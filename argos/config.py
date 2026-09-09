from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    data_dir: Path

    @property
    def database(self) -> Path:
        return self.data_dir / "argos.sqlite3"

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    def ensure(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)


def default_paths(data_dir: str | None = None) -> AppPaths:
    configured = data_dir or os.environ.get("ARGOS_DATA_DIR")
    location = Path(configured) if configured else Path.cwd() / ".argos"
    return AppPaths(location.expanduser().resolve())
