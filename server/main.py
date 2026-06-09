from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from database import engine, Base
from api import auth, projects, api_cases, ui_cases, api_test_cases, environments, test_runner, batch_runs, ws_batch, test_suites, scene_nodes, ai_generate, ai_skills, ui_recordings, ws_ui_record, ui_runner, ws_ui_run, ws_ui_preview, monkey, ws_monkey, dashboard, ui_test_suites

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
app.include_router(api_test_cases.router, prefix=f"{settings.API_V1_STR}/api-test-cases", tags=["api-test-cases"])
app.include_router(environments.router, prefix=f"{settings.API_V1_STR}/environments", tags=["environments"])
app.include_router(test_runner.router, prefix=f"{settings.API_V1_STR}/test-runner", tags=["test-runner"])
app.include_router(batch_runs.router, prefix=f"{settings.API_V1_STR}/batch-runs", tags=["batch-runs"])
app.include_router(ws_batch.router, tags=["websocket"])
app.include_router(test_suites.router, prefix=f"{settings.API_V1_STR}/test-suites", tags=["test-suites"])
app.include_router(scene_nodes.router, prefix=f"{settings.API_V1_STR}/scene-nodes", tags=["scene-nodes"])
app.include_router(ai_generate.router, prefix=f"{settings.API_V1_STR}/ai-generate", tags=["ai-generate"])
app.include_router(ai_skills.router, prefix=f"{settings.API_V1_STR}/ai-skills", tags=["ai-skills"])
app.include_router(ui_recordings.router, prefix=f"{settings.API_V1_STR}/ui-recordings", tags=["ui-recordings"])
app.include_router(ws_ui_record.router, tags=["websocket"])
app.include_router(ws_ui_run.router, tags=["websocket"])
app.include_router(ws_ui_preview.router, tags=["websocket"])
app.include_router(ui_runner.router, prefix=f"{settings.API_V1_STR}/ui-runner", tags=["ui-runner"])
app.include_router(monkey.router, prefix=f"{settings.API_V1_STR}/monkey", tags=["monkey"])
app.include_router(ws_monkey.router, tags=["websocket"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(ui_test_suites.router, prefix=f"{settings.API_V1_STR}/ui-test-suites", tags=["ui-test-suites"])

# 自动重定向斜杠（确保 /api/v1/ui-cases 和 /api/v1/ui-cases/ 都能访问）
# app.router.redirect_slashes = False


@app.get("/")
def root():
    return {"message": "Testing Platform API", "version": settings.VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
