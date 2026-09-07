from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from services.excel_service import create_template_if_missing
from routes import router
from services.storage_service import ensure_runtime_directories


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    ensure_runtime_directories(BASE_DIR)
    create_template_if_missing(BASE_DIR)

    app = FastAPI(title="excel-input-sample-app-poc")
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    app.include_router(router)
    return app


app = create_app()
