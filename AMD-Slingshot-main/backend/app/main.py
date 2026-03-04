from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import ping_database
from app.routers.analyze import router as analyze_router
from app.routers.history import router as history_router
from app.services.firebase_service import initialize_firebase


logger = logging.getLogger(__name__)


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_path = Path(settings.upload_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

app.include_router(analyze_router)
app.include_router(history_router)


@app.on_event("startup")
async def on_startup() -> None:
    try:
        initialize_firebase()
    except Exception:
        logger.exception("Firebase initialization failed during startup; continuing")
    try:
        await ping_database()
    except Exception:
        logger.exception("Database ping failed during startup")
        if settings.require_db_on_startup:
            raise


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.get("/diag")
def diagnostics() -> dict:
    """Return deployment diagnostics — helps debug production issues."""
    import importlib
    from pathlib import Path as _P

    model_dir = _P(__file__).resolve().parents[1] / "model_assets"
    smart_agri_pth = model_dir / "smart_agri" / "soil_model.pth"
    ml1_dir = model_dir / "ML1" / "ML1" / "soil_models_gpu"

    torch_available = False
    try:
        importlib.import_module("torch")
        torch_available = True
    except Exception:
        pass

    scipy_available = False
    try:
        importlib.import_module("scipy")
        scipy_available = True
    except Exception:
        pass

    sklearn_available = False
    try:
        importlib.import_module("sklearn")
        sklearn_available = True
    except Exception:
        pass

    return {
        "version": "d8cb6195-fix2",
        "environment": settings.environment,
        "allow_dev_auth_bypass": settings.allow_dev_auth_bypass,
        "auth_bypass_active": not settings.firebase_service_account_json or (settings.environment != "production" and settings.allow_dev_auth_bypass),
        "cors_origins": settings.allowed_origins,
        "mongo_configured": settings.mongo_uri is not None and len(settings.mongo_uri) > 10,
        "firebase_sa_configured": settings.firebase_service_account_json is not None,
        "smart_agri_model_exists": smart_agri_pth.exists(),
        "smart_agri_model_size_mb": round(smart_agri_pth.stat().st_size / 1048576, 1) if smart_agri_pth.exists() else 0,
        "ml1_dir_exists": ml1_dir.exists(),
        "ml1_files": sorted(f.name for f in ml1_dir.iterdir()) if ml1_dir.exists() else [],
        "torch_available": torch_available,
        "scipy_available": scipy_available,
        "sklearn_available": sklearn_available,
    }
