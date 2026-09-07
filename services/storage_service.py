from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date as date_cls, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from services.errors import StorageError
from services.roster_service import roster_lookup


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_NAME = "data"


@dataclass(frozen=True)
class NormalizedRecord:
    date: str
    employee_number: str
    employee_name: str
    reason: str
    start_time: str
    end_time: str
    remarks: str

    def to_dict(self) -> dict[str, str]:
        return {
            "date": self.date,
            "employee_number": self.employee_number,
            "employee_name": self.employee_name,
            "reason": self.reason,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "remarks": self.remarks,
        }


def ensure_runtime_directories(base_dir: Path) -> None:
    (base_dir / DATA_DIR_NAME).mkdir(parents=True, exist_ok=True)
    (base_dir / "backup").mkdir(parents=True, exist_ok=True)
    (base_dir / "static").mkdir(parents=True, exist_ok=True)
    (base_dir / "static" / "css").mkdir(parents=True, exist_ok=True)
    (base_dir / "static" / "js").mkdir(parents=True, exist_ok=True)
    (base_dir / "templates").mkdir(parents=True, exist_ok=True)


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def validate_date(value: str) -> str:
    if not value:
        raise ValueError("date is required")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("date must be YYYY-MM-DD") from exc
    return value


def validate_time(value: str, field_name: str, allow_blank: bool = True) -> str:
    if not value:
        if allow_blank:
            return ""
        raise ValueError(f"{field_name} is required")
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be HH:MM") from exc
    return value


def normalize_payload(base_dir: Path, payload: dict[str, Any]) -> tuple[NormalizedRecord, str]:
    target_date = validate_date(normalize_text(payload.get("date")))
    employee_name = normalize_text(payload.get("employee_name"))
    if not employee_name:
        raise ValueError("employee_name is required")
    employee_number = normalize_text(payload.get("employee_number"))
    reason = normalize_text(payload.get("reason"))
    start_time = validate_time(normalize_text(payload.get("start_time")), "start_time")
    end_time = validate_time(normalize_text(payload.get("end_time")), "end_time")
    remarks = normalize_text(payload.get("remarks"))

    if start_time and end_time:
        start_minutes = _minutes_since_midnight(start_time)
        end_minutes = _minutes_since_midnight(end_time)
        if end_minutes < start_minutes:
            raise ValueError("end_time must not be earlier than start_time")

    warning = ""
    roster = roster_lookup(base_dir)
    if not employee_number and employee_name in roster and roster[employee_name]["employee_number"]:
        employee_number = roster[employee_name]["employee_number"]
    elif employee_number and employee_number in roster:
        roster_name = roster[employee_number]["employee_name"]
        if roster_name != employee_name:
            warning = (
                f"employee_number {employee_number} is registered to '{roster_name}' in the roster; "
                f"using the roster name instead of the entered '{employee_name}'."
            )
        employee_name = roster_name

    record = NormalizedRecord(
        date=target_date,
        employee_number=employee_number,
        employee_name=employee_name,
        reason=reason,
        start_time=start_time,
        end_time=end_time,
        remarks=remarks,
    )
    return record, warning


def data_file_path(base_dir: Path, target_date: str) -> Path:
    return base_dir / DATA_DIR_NAME / f"{target_date}.json"


def output_file_path(base_dir: Path, target_date: str) -> Path:
    return base_dir / f"{target_date}.xlsx"


def load_records_for_date(base_dir: Path, target_date: str) -> list[dict[str, str]]:
    path = data_file_path(base_dir, target_date)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StorageError(f"invalid data file: {path.name}") from exc
    if not isinstance(data, list):
        raise StorageError(f"invalid record list in {path.name}")
    records: list[dict[str, str]] = []
    for item in data:
        if isinstance(item, dict):
            records.append(
                {
                    "date": normalize_text(item.get("date")),
                    "employee_number": normalize_text(item.get("employee_number")),
                    "employee_name": normalize_text(item.get("employee_name")),
                    "reason": normalize_text(item.get("reason")),
                    "start_time": normalize_text(item.get("start_time")),
                    "end_time": normalize_text(item.get("end_time")),
                    "remarks": normalize_text(item.get("remarks")),
                }
            )
    return records


def list_records(base_dir: Path, target_date: str | None) -> list[dict[str, str]]:
    if target_date:
        validate_date(target_date)
        return load_records_for_date(base_dir, target_date)

    records: list[dict[str, str]] = []
    data_dir = base_dir / DATA_DIR_NAME
    if not data_dir.exists():
        return records
    for path in sorted(data_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise StorageError(f"invalid data file: {path.name}") from exc
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.append(
                        {
                            "date": normalize_text(item.get("date")),
                            "employee_number": normalize_text(item.get("employee_number")),
                            "employee_name": normalize_text(item.get("employee_name")),
                            "reason": normalize_text(item.get("reason")),
                            "start_time": normalize_text(item.get("start_time")),
                            "end_time": normalize_text(item.get("end_time")),
                            "remarks": normalize_text(item.get("remarks")),
                        }
                    )
    return records


def save_records_for_date(base_dir: Path, target_date: str, records: list[dict[str, str]]) -> None:
    path = data_file_path(base_dir, target_date)
    payload = json.dumps(records, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def save_record(base_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    record, roster_warning = normalize_payload(base_dir, payload)
    existing = load_records_for_date(base_dir, record.date)
    key = record.employee_number or record.employee_name
    replaced = False
    updated: list[dict[str, str]] = []
    for item in existing:
        item_key = normalize_text(item.get("employee_number")) or normalize_text(item.get("employee_name"))
        if item_key == key:
            updated.append(record.to_dict())
            replaced = True
        else:
            updated.append(item)
    if not replaced:
        updated.append(record.to_dict())
    save_records_for_date(base_dir, record.date, updated)

    warnings = []
    if not record.employee_number:
        warnings.append("employee_number is empty; matched by employee_name.")
    if roster_warning:
        warnings.append(roster_warning)
    warning = " ".join(warnings)

    return {
        "message": "保存しました。",
        "warning": warning,
        "item": record.to_dict(),
    }


def _minutes_since_midnight(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)
