import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Silence Windows-specific ProactorEventLoop connection lost errors (WinError 10054)
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        _orig_call_connection_lost = getattr(_ProactorBasePipeTransport, "_call_connection_lost", None)

        if callable(_orig_call_connection_lost):
            _orig_callable = _orig_call_connection_lost

            def _safe_call_connection_lost(self, exc=None):
                try:
                    _orig_callable(self, exc)
                except ConnectionResetError:
                    pass

            setattr(_ProactorBasePipeTransport, "_call_connection_lost", _safe_call_connection_lost)
    except Exception:
        pass

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routes.location import router as location_router
from backend.routes.prediction import router as prediction_router
from backend.routes.properties import router as properties_router
from backend.routes.trends import router as trends_router
from backend.routes.image_analysis import router as image_router
from backend.routes.auth import router as auth_router
from backend.routes.assistant import router as assistant_router
from backend.routes.neighborhood import router as neighborhood_router

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="GeoEstate AI - MakaanX",
    description="Multimodal Real Estate Valuation & Investment Intelligence Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router)
app.include_router(location_router)
app.include_router(properties_router)
app.include_router(trends_router)
app.include_router(image_router)
app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(neighborhood_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "MakaanX",
        "message": "Real property dataset loaded from the project dataset for local market intelligence.",
    }


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
