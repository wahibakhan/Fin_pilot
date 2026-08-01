from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1.ai_chat import router as ai_chat_router
from src.api.v1.audit_logs import router as audit_logs_router
from src.api.v1.auth import router as auth_router
from src.api.v1.categories import router as categories_router
from src.api.v1.dashboard import router as dashboard_router
from src.api.v1.expenses import router as expenses_router
from src.api.v1.health import router as health_router
from src.api.v1.income import router as income_router
from src.api.v1.ledger import router as ledger_router
from src.api.v1.reports import router as reports_router
from src.core.config import get_settings
from src.core.exceptions import (
    AIServiceUnavailableError,
    AppError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

settings = get_settings()

_STATUS_BY_ERROR = {
    ValidationError: 400,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    AIServiceUnavailableError: 503,
}


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(exc), 400)
        body: dict[str, object] = {"detail": exc.message}
        if exc.field:
            body["field"] = exc.field
        return JSONResponse(status_code=status_code, content=body)

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(categories_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(expenses_router, prefix="/api/v1")
    app.include_router(income_router, prefix="/api/v1")
    app.include_router(ledger_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(ai_chat_router, prefix="/api/v1")
    app.include_router(audit_logs_router, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
