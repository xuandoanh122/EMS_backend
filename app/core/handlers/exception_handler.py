"""
Global exception handlers for the FastAPI application.
Registers handlers that catch all EMSException subclasses and convert them
to the standardized API response format.

Also handles unexpected exceptions, Pydantic validation errors,
and generic HTTP exceptions.
"""

import logging
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.base import EMSException
from app.core.response import APIResponse

logger = logging.getLogger("ems.exception_handler")


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI app instance.
    Call this function in main.py after creating the app.
    """

    @app.exception_handler(EMSException)
    async def ems_exception_handler(
        request: Request, exc: EMSException
    ) -> JSONResponse:
        """
        Handle all custom EMS exceptions.
        Returns the standardized API response format.
        """
        logger.warning(
            "EMSException [%s] %s - %s | Path: %s",
            exc.status_code,
            exc.message,
            exc.detail,
            request.url.path,
        )

        response = APIResponse.error(
            code=exc.status_code,
            message=exc.message,
            detail=exc.detail,
        )

        response_dict = response.model_dump()

        # Include additional errors if present (e.g., validation field errors)
        if exc.errors is not None:
            response_dict["errors"] = exc.errors

        return JSONResponse(
            status_code=exc.status_code,
            content=response_dict,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic/FastAPI request validation errors.
        Converts the raw validation errors into the standardized format.
        """
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
            )

        logger.warning(
            "ValidationError | Path: %s | Errors: %s",
            request.url.path,
            errors,
        )

        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "Validation Error",
                "detail": "The request data failed validation",
                "data": None,
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handle generic Starlette/FastAPI HTTP exceptions (404, 405, etc.).
        """
        logger.warning(
            "HTTPException [%s] %s | Path: %s",
            exc.status_code,
            exc.detail,
            request.url.path,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": "HTTP Error",
                "detail": str(exc.detail) if exc.detail else "An HTTP error occurred",
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for any unhandled exceptions.
        Logs the full traceback and returns a generic 500 error.
        Prevents leaking internal error details to the client.
        """
        logger.error(
            "Unhandled Exception | Path: %s | Error: %s",
            request.url.path,
            str(exc),
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal Server Error",
                "detail": "An unexpected error occurred. Please try again later",
                "data": None,
            },
        )
