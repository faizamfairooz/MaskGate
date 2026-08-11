from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    message: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify API is running."""
    return HealthResponse(status="healthy", message="MaskGate API is running")


@router.get("/database", response_model=HealthResponse)
async def database_health():
    """Check database connection health."""
    try:
        from backend.app.database.connection import get_database_connection, release_connection

        conn = get_database_connection()
        try:
            import psycopg2
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return HealthResponse(status="healthy", message="Database connection successful")
        finally:
            release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
