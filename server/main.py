from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from database import engine, Base
from api import auth, projects, api_cases, ui_cases

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(api_cases.router, prefix=f"{settings.API_V1_STR}/api-cases", tags=["api-cases"])
app.include_router(ui_cases.router, prefix=f"{settings.API_V1_STR}/ui-cases", tags=["ui-cases"])


@app.get("/")
def root():
    return {"message": "Testing Platform API", "version": settings.VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
