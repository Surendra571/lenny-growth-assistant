from typing import Any, Optional
from fastapi import HTTPException, status


class AppBaseException(HTTPException):
    """
    Base class for structured application exceptions.
    """
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details


class ConfigurationException(AppBaseException):
    def __init__(self, message: str = "Invalid system or provider configuration.", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="CONFIGURATION_ERROR",
            message=message,
            details=details,
        )


class ResourceNotFoundException(AppBaseException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=message,
            details=details,
        )


class SessionNotFoundException(ResourceNotFoundException):
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session with ID '{session_id}' not found.",
            details={"session_id": session_id},
        )


class ArtifactNotFoundException(ResourceNotFoundException):
    def __init__(self, artifact_id: str):
        super().__init__(
            message=f"Artifact with ID '{artifact_id}' not found.",
            details={"artifact_id": artifact_id},
        )


class ModelUnavailableException(AppBaseException):
    def __init__(self, message: str = "The configured model provider is currently unavailable.", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="MODEL_UNAVAILABLE",
            message=message,
            details=details,
        )


class ModelTimeoutException(AppBaseException):
    def __init__(self, message: str = "Inference request to model provider timed out.", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="MODEL_TIMEOUT",
            message=message,
            details=details,
        )


class RetrievalException(AppBaseException):
    def __init__(self, message: str = "Failed to retrieve transcript knowledge from vector store.", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="RETRIEVAL_FAILED",
            message=message,
            details=details,
        )


class UnsafeArtifactException(AppBaseException):
    def __init__(self, message: str = "Generated artifact failed security sanitization policies.", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_ARTIFACT_REJECTED",
            message=message,
            details=details,
        )

