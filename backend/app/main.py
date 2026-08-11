import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.routes import health
from app.api.routes.schema import router as schema_router
from app.config.settings import settings
from app.database.connection import close_all_connections, initialize_connection_pool

API_V1 = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_connection_pool()
    except Exception as e:
        print(f"Warning: Database connection pool initialization failed: {e}")
    yield
    close_all_connections()


app = FastAPI(
    title="MaskGate API",
    description="AI-powered database security platform for sensitive data detection and masking",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router, prefix=f"{API_V1}/health", tags=["health"])
app.include_router(schema_router, prefix=f"{API_V1}/schema", tags=["schema"])


@app.get("/")
async def root():
    return {"message": "MaskGate API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
