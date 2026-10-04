"""
MR.GREEN — Application Entry Point

FastAPI application with all routes, middleware, and lifecycle management.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import close_db, init_db

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle — startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("  MR.GREEN — Starting up")
    logger.info("  Environment: %s", settings.app_env)
    logger.info("  AI Model: %s @ %s", settings.ollama_model, settings.ollama_base_url)
    logger.info("=" * 60)

    # Initialize database tables and sync registered tools
    try:
        await init_db()
        logger.info("Database initialized successfully")
        from app.database.session import async_session_factory
        from app.tools.registry import tool_registry
        async with async_session_factory() as session:
            await tool_registry.sync_to_db(session)
        logger.info("Synchronized %d tools to database", tool_registry.count)
    except Exception as e:
        logger.error("Database initialization failed: %s", str(e))
        logger.warning("MR.GREEN starting without database — some features will be unavailable")

    yield

    # Shutdown
    logger.info("MR.GREEN — Shutting down")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MR.GREEN",
        description="Autonomous Personal AI Agent",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS middleware (for frontend communication)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",    # Vite dev server
            "http://localhost:3000",    # Alternative dev server
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_origin_regex=r"^https?://.*$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from app.api.routes.health import router as health_router
    from app.api.routes.chat import router as chat_router
    from app.api.routes.conversations import router as conversations_router
    from app.api.routes.memory import router as memory_router
    from app.api.routes.daily_logs import router as daily_logs_router
    from app.api.routes.tools import router as tools_router
    from app.api.routes.capabilities import router as capabilities_router
    from app.api.routes.agent_runs import router as agent_runs_router
    from app.api.routes.approvals import router as approvals_router
    from app.voice.websocket import router as voice_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(chat_router, tags=["Chat"])
    app.include_router(conversations_router, tags=["Conversations"])
    app.include_router(memory_router, tags=["Memory"])
    app.include_router(daily_logs_router, tags=["Daily Logs"])
    app.include_router(tools_router, tags=["Tools"])
    app.include_router(capabilities_router, tags=["Capabilities"])
    app.include_router(agent_runs_router, tags=["Agent Runs"])
    app.include_router(approvals_router, tags=["Approvals"])
    app.include_router(voice_router, tags=["Voice"])

    # Mount frontend static files if available (serves PWA mobile interface)
    static_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static")),
        "/app/static",
    ]
    for s_dir in static_dirs:
        if os.path.isdir(s_dir) and os.path.exists(os.path.join(s_dir, "index.html")):
            logger.info("Serving frontend static files from: %s", s_dir)
            from fastapi.staticfiles import StaticFiles
            app.mount("/", StaticFiles(directory=s_dir, html=True), name="frontend")
            break

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
    )
