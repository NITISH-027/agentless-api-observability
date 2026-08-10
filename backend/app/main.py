import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import Base, engine
import app.models  # Ensure models register on Base metadata
from app.api.routes import health, logs, github_routes

# Setup logging immediately on module load
setup_logging()
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing API Observability & Debugging Platform Backend...")
    try:
        settings = get_settings()
        logger.info(f"Configuration loaded successfully. LLM Provider: {settings.LLM_PROVIDER}")
        
        # Create database tables automatically
        logger.info("Creating database tables if not existing...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database or settings during startup: {e}")
    yield
    logger.info("Shutting down API Observability & Debugging Platform Backend...")

app = FastAPI(
    title="Agentless API Observability & Debugging Platform Backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS setup for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(logs.router)
app.include_router(github_routes.router)


