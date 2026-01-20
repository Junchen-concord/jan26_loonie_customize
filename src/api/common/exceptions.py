from fastapi import Request
from fastapi.responses import JSONResponse


class BadRequestError(Exception):
    def __init__(self, detail: str, code: str = "BAD_REQUEST"):
        self.detail = detail
        self.code = code


class NotFoundError(Exception):
    def __init__(self, detail: str, code: str = "NOT_FOUND"):
        self.detail = detail
        self.code = code


class InternalServerError(Exception):
    def __init__(self, detail: str, code: str = "INTERNAL_SERVER_ERROR"):
        self.detail = detail
        self.code = code


class ConflictError(Exception):
    def __init__(self, detail: str, code: str = "CONFLICT"):
        self.detail = detail
        self.code = code


class UnauthorizedError(Exception):
    def __init__(self, detail: str, code: str = "UNAUTHORIZED"):
        self.detail = detail
        self.code = code


class ForbiddenError(Exception):
    def __init__(self, detail: str, code: str = "FORBIDDEN"):
        self.detail = detail
        self.code = code


class UnprocessableEntityError(Exception):
    def __init__(self, detail: str, code: str = "UNPROCESSABLE_ENTITY"):
        self.detail = detail
        self.code = code


class common404Exception(Exception):
    def __init__(self, title: str, detail: str):
        self.title = (title,)
        self.detail = (detail,)


class common400Exception(Exception):
    def __init__(self, title: str, detail: str):
        self.title = (title,)
        self.detail = (detail,)


class common500Exception(Exception):
    def __init__(self, title: str, detail: str):
        self.title = (title,)
        self.detail = (detail,)


def create_exception_handler(status_code):
    async def handler(request: Request, exc):  # noqa: ARG001
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.detail, "code": exc.code},
        )

    return handler


def register_exception_handlers(app):
    exception_map = {
        NotFoundError: 404,
        BadRequestError: 400,
        InternalServerError: 500,
        ConflictError: 409,
        UnauthorizedError: 401,
        ForbiddenError: 403,
        UnprocessableEntityError: 422,
    }

    for exc_class, status_code in exception_map.items():
        app.add_exception_handler(exc_class, create_exception_handler(status_code))
