from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import AppBaseException
from app.core.logging import logger, setup_logging
from app.db.session import check_db_health, engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    """
    setup_logging()
    logger.info(f"Starting Lenny Growth Assistant Backend [Env: {settings.ENVIRONMENT}]")
    logger.info(f"Active LLM Provider: {settings.LLM_PROVIDER}")
    
    # Initialize and verify database persistence
    await init_db()

    yield

    logger.info("Shutting down Lenny Growth Assistant Backend...")
    await engine.dispose()
    logger.info("Database engine connections disposed.")


app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Agentic conversational backend powering grounded product and growth wisdom from Lenny's Podcast.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Global Exception Handlers
@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(f"Unhandled server error [Request: {request_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
                "details": None,
            }
        },
    )


from app.api.v1.router import api_v1_router, api_router


# Root Health & Readiness Routes & API Routers Mounting
app.include_router(health_router)
app.include_router(api_v1_router)
app.include_router(api_router)

