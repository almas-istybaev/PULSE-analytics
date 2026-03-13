"""
Централизованная обработка ошибок API.

Регистрирует обработчики для HTTPException и RequestValidationError,
возвращая единый формат ответа ошибки из spec.md (раздел 13).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует глобальные обработчики ошибок на FastAPI-приложении.

    Все ошибки возвращаются в стандартном формате:
    { "error": { "code": "...", "message": "...", "details": {...} } }

    Args:
        app: Экземпляр FastAPI приложения.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Обрабатывает HTTPException, возвращая стандартный JSON-формат ошибки.

        Args:
            request: Входящий HTTP запрос.
            exc: Экземпляр HTTPException.

        Returns:
            JSONResponse с полем 'error'.
        """
        # Если detail уже словарь с нашим форматом — используем как есть
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            error_body = exc.detail
        else:
            # Иначе оборачиваем строку
            error_body = {
                "code": _status_to_code(exc.status_code),
                "message": str(exc.detail),
                "details": {},
            }
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_body},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Обрабатывает ошибки валидации Pydantic (422 Unprocessable Entity).

        Args:
            request: Входящий HTTP запрос.
            exc: Экземпляр RequestValidationError.

        Returns:
            JSONResponse с деталями ошибок валидации.
        """
        errors = []
        for err in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
                "message": err["msg"],
                "type": err["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Перехватывает все необработанные исключения (500 Internal Server Error).

        WARNING: Этот обработчик скрывает трассировку от клиента.
        Детали ошибки логируются через structlog.

        Args:
            request: Входящий HTTP запрос.
            exc: Любое необработанное исключение.

        Returns:
            JSONResponse с кодом 500.
        """
        import structlog
        log = structlog.get_logger()
        log.error("Unhandled exception", exc_info=exc, path=str(request.url))

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )


def _status_to_code(status_code: int) -> str:
    """Преобразует HTTP-статус в строковый код ошибки.

    Args:
        status_code: HTTP статус-код.

    Returns:
        Строковый код ошибки для API-ответа.
    """
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")
