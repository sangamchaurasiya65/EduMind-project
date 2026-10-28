from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routers.health import router as health_router
from backend.app.routers.materials import router as materials_router
from backend.app.routers.quizzes import router as quizzes_router, quiz_alias_router
from backend.app.routers.attempts import router as attempts_router
from backend.app.routers.competency import router as competency_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.study_sessions import router as study_sessions_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.subjects import router as subjects_router
from backend.app.routers.profile import router as profile_router
from backend.app.routers.chat import router as chat_router




@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database tables on application startup.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_TITLE,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, prefix="/api")
app.include_router(health_router)  # Also expose /health for cloud platforms & container healthchecks
app.include_router(materials_router, prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(quiz_alias_router, prefix="/api")
app.include_router(attempts_router, prefix="/api")
app.include_router(competency_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(study_sessions_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(chat_router, prefix="/api")




@app.get("/", tags=["Root"])
def root_info():
    """Root metadata endpoint with pointers to documentation and health status."""
    return {
        "project": settings.PROJECT_NAME,
        "title": settings.PROJECT_TITLE,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )
