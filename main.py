from fastapi import FastAPI
from database.database import db_manager

app = FastAPI()

@app.on_event("startup")
async def startup():
    await db_manager.initialize()

@app.get("/health")
async def health():
    is_healthy = await db_manager.health_check()
    if is_healthy:
        return {"status": "healthy"}
    return {"status": "unhealthy"}

@app.get("/")
async def root():
    return {"message": "Eyewear OMS API running"}