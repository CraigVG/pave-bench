from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import Case, load_case_from_metadata


@dataclass(frozen=True)
class ManifestRow:
    case_id: str
    split: str
    tasks: list[str]
    metadata_path: Path
    case: Case
    tags: list[str]
    raw: dict[str, Any]


def load_manifest(path: str | Path) -> list[ManifestRow]:
    manifest_path = Path(path)
    base_dir = manifest_path.parent
    rows: list[ManifestRow] = []

    for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        metadata_value = raw.get("metadataPath")
        if not metadata_value:
            raise ValueError(f"Manifest row {line_number} is missing metadataPath")
        metadata_path = Path(metadata_value)
        if not metadata_path.is_absolute():
            metadata_path = base_dir / metadata_path
        case = load_case_from_metadata(metadata_path)
        case_id = str(raw.get("caseId", case.case_id))
        if case_id != case.case_id:
            raise ValueError(f"Manifest row {line_number} caseId={case_id} does not match metadata caseId={case.case_id}")
        rows.append(
            ManifestRow(
                case_id=case_id,
                split=str(raw.get("split", "unspecified")),
                tasks=[str(task) for task in raw.get("tasks", [])],
                metadata_path=metadata_path,
                case=case,
                tags=[str(tag) for tag in raw.get("tags", [])],
                raw=dict(raw),
            )
        )
    return rows
