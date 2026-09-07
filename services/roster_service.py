from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.errors import StorageError


def roster_path(base_dir: Path) -> Path:
    return base_dir / "roster.json"


def load_roster(base_dir: Path) -> list[dict[str, str]]:
    path = roster_path(base_dir)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StorageError(f"invalid roster file: {path.name}") from exc
    roster: list[dict[str, str]] = []
    for item in data:
        employee_number = str(item.get("employee_number", "")).strip()
        employee_name = str(item.get("employee_name", "")).strip()
        if employee_name:
            roster.append(
                {
                    "employee_number": employee_number,
                    "employee_name": employee_name,
                }
            )
    return roster


def roster_lookup(base_dir: Path) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for item in load_roster(base_dir):
        name = item["employee_name"]
        number = item["employee_number"]
        lookup[name] = {"employee_number": number, "employee_name": name}
        if number:
            lookup[number] = {"employee_number": number, "employee_name": name}
    return lookup
