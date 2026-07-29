import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.openai_routes import router as openai_router
from backend.api.gateway import router as gateway_router
from backend.api.websocket import router as ws_router
from backend.api.agent_routes import router as agent_router
from backend.config import get_settings
import backend.agents  # Trigger automatic agent registration


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield
    print("Shutting down...")


app = FastAPI(
    title="AI20K Agent",
    description="AI Agent built with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(openai_router, prefix="/v1")
app.include_router(gateway_router)
app.include_router(ws_router)
app.include_router(agent_router)


from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


# Phục vụ Web UI với đường dẫn tuyệt đối độc lập CWD
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")
