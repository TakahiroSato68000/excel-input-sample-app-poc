from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.errors import ExcelGenerationError, StorageError
from services.excel_service import confirm_records
from services.roster_service import load_roster
from services.storage_service import (
    BASE_DIR,
    list_records,
    save_record,
    validate_date,
)


router = APIRouter()
INDEX_FILE = BASE_DIR / "templates" / "index.html"


@router.get("/")
def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@router.get("/api/roster")
def roster() -> dict[str, list[dict[str, str]]]:
    try:
        items = load_roster(BASE_DIR)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@router.get("/api/entries")
def entries(date: str | None = None) -> dict[str, Any]:
    try:
        items = list_records(BASE_DIR, date)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@router.post("/api/entries")
def create_entry(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        result = save_record(BASE_DIR, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@router.post("/api/confirm")
def confirm(payload: dict[str, Any]) -> dict[str, Any]:
    target_date = str(payload.get("date", "")).strip()
    if not target_date:
        raise HTTPException(status_code=400, detail="date is required")
    try:
        validate_date(target_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        result = confirm_records(BASE_DIR, target_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (StorageError, ExcelGenerationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result
