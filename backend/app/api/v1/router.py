from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.messages import router as messages_router
from app.api.v1.artifacts import router as artifacts_router

api_v1_router = APIRouter(prefix="/api/v1")
api_router = APIRouter(prefix="/api")

# Mount all domain sub-routers
for r in [api_v1_router, api_router]:
    r.include_router(health_router)
    r.include_router(sessions_router)
    r.include_router(messages_router)
    r.include_router(artifacts_router)

