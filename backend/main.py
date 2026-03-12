from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from .config import settings
from .routers import tasks
from .auth import router as auth_router

app = FastAPI(
    title="Tact AI",
    description="AI-based scheduler using Eisenhower matrix",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# Include routers
app.include_router(auth_router)
app.include_router(tasks.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
