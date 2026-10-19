from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, model_validator

from constants import DATE_DIR_FORMAT
from schemas import Location


def _validate_relative_subpath(subpath: str, error_prefix: str) -> str:
    clean = subpath.strip().strip("/")
    parts = Path(clean).parts
    if (
        not clean
        or clean in (".", "..")
        or any(part == ".." for part in parts)
        or Path(clean).is_absolute()
    ):
        raise ValueError(f"{error_prefix}: '{subpath}'")
    return clean


class TransferConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_host: str
    username: Optional[str] = None
    destination_subdir: str = "f200/arina"
    distiller_root: Optional[str] = None

    @model_validator(mode="after")
    def validate_paths(self) -> "TransferConfig":
        self.destination_subdir = _validate_relative_subpath(
            self.destination_subdir, "Invalid destination_subdir"
        )
        if not self.source_host.strip():
            raise ValueError("source_host must not be blank")
        if self.username is not None and not self.username.strip():
            raise ValueError("username must not be blank")
        return self


def resolve_destination_path(
    distiller_root: str,
    destination_subdir: str,
    created_datetime: datetime,
    scan_id: int,
) -> str:
    """Resolve destination directory layout.

    Layout: <distiller-root>/f200/arina/<YYYY.MM.DD>/<Scan.id>/
    """
    root = Path(distiller_root).resolve()
    clean_subdir = _validate_relative_subpath(
        destination_subdir, "Unsafe destination_subdir escapes root"
    )

    date_dir = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)
    dest = (root / clean_subdir / date_dir / str(scan_id)).resolve()
    if not dest.is_relative_to(root):
        raise ValueError(f"Destination path escapes distiller_root: '{dest}'")
    return str(dest)


def prepare_transfer_files(locations: List[Location]) -> List[Tuple[str, str]]:
    """Return source paths and destinations relative to the master directory."""
    if not locations:
        raise ValueError("No source locations to transfer")
    paths = [Path(loc.path) for loc in locations]
    if any(not p.is_absolute() or ".." in p.parts for p in paths):
        raise ValueError(
            "Source locations must be absolute Linux paths without traversal"
        )
    if any(any(c in str(p) for c in ("\n", "\r", "\0")) for p in paths):
        raise ValueError("Source paths must not contain line breaks or NUL")
    master = next((p for p in paths if p.name.endswith("master.h5")), paths[0])
    files = []
    seen = set()
    for path in paths:
        relative = path.relative_to(master.parent).as_posix()
        if relative in seen:
            raise ValueError(f"Destination path collision detected: {relative}")
        seen.add(relative)
        files.append((str(path), relative))
    return files
