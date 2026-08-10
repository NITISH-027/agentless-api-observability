from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Dict, Any, Optional

class RequestSchema(BaseModel):
    method: str = Field(..., description="HTTP request method")
    path: str = Field(..., description="HTTP request route/path")
    query: Optional[Dict[str, Any]] = Field(default_factory=dict)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    body: Optional[Any] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        val = v.upper().strip()
        if val not in allowed:
            raise ValueError(f"HTTP method '{v}' is not supported. Must be one of {allowed}")
        return val

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Request path cannot be empty")
        return v.strip()

class ResponseSchema(BaseModel):
    status_code: int = Field(..., description="HTTP response status code")
    body: Optional[Any] = None

    @field_validator("status_code")
    @classmethod
    def validate_status_code(cls, v: int) -> int:
        if not (100 <= v <= 599):
            raise ValueError(f"HTTP Status code must be between 100 and 599. Got {v}")
        return v

class ErrorSchema(BaseModel):
    type: str = Field(..., description="Error or exception class name")
    message: str = Field(..., description="Human readable description of the error")
    stack_trace: str = Field(..., description="Source code traceback lines")

    @field_validator("stack_trace")
    @classmethod
    def validate_stack_trace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Stack trace must be a non-empty string")
        return v

class MetadataSchema(BaseModel):
    request_id: Optional[str] = None
    deployment_id: Optional[str] = None
    git_commit: Optional[str] = None

class IngestionLogPayload(BaseModel):
    service: str = Field(..., description="Name of the service")
    environment: str = Field(..., description="Target runtime environment")
    timestamp: datetime = Field(..., description="ISO datetime of the incident")
    request: RequestSchema
    response: ResponseSchema
    error: ErrorSchema
    metadata: Optional[MetadataSchema] = Field(default_factory=MetadataSchema)

    @field_validator("service")
    @classmethod
    def validate_service(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Service name cannot be empty")
        return v.strip()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Environment cannot be empty")
        return v.strip()
