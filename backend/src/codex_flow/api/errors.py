"""Stable HTTP error helpers for API routes."""

from fastapi import HTTPException

from codex_flow.api.schemas import ErrorBody, ErrorResponse


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=ErrorBody(code=code, message=message)).model_dump(),
    )


def not_found(code: str, message: str) -> HTTPException:
    return api_error(404, code, message)


def conflict(code: str, message: str) -> HTTPException:
    return api_error(409, code, message)


def invalid_request(code: str, message: str) -> HTTPException:
    return api_error(400, code, message)


def unprocessable(code: str, message: str) -> HTTPException:
    """Build the stable 422 envelope used for invalid control state/actions."""
    return api_error(422, code, message)
