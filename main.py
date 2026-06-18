from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from logger.logger import get_logger, log_info, log_error, log_exception
from database.database import db_manager, health_check
from api.users import user_router
from api.sla_store import router as sla_store_router
from api.order import router as order_router

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting OptiFlow AI...")
    await db_manager.initialize()
    logger.info("Database initialized with connection pooling")
    yield
    logger.info("Shutting down...")
    await db_manager.close_all()
    logger.info("Database connections closed")

app = FastAPI(
    title="OptiFlow AI",
    description="AI-Powered Order Management System for Eyewear Brand",
    version="1.0.0",
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.)
    allow_headers=["*"],   # Allow all headers
)

app.include_router(user_router)
app.include_router(sla_store_router)
app.include_router(order_router)


@app.get("/health")
async def health():
    ok = await health_check()
    return {
        "status": "healthy" if ok else "unhealthy",
        "database": "connected" if ok else "disconnected",
        "service": "OptiFlow AI"
    }

@app.get("/")
async def root():
    return {
        "message": "OptiFlow AI is running",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "health": "/health"
        }
    }