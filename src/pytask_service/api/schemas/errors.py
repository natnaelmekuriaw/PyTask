from pydantic import Field

from pytask_service.api.schemas.base import APIModel


class ErrorDetail(APIModel):
    location: list[str | int]
    message: str
    type: str


class ErrorBody(APIModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(APIModel):
    error: ErrorBody
