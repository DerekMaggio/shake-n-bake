"""Custom exceptions for shake-n-bake."""


class ShakeNBakeError(Exception):
    """Base exception for shake-n-bake errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class ConfigurationError(ShakeNBakeError):
    """Configuration validation or loading errors."""

    pass


class DockerError(ShakeNBakeError):
    """Docker operation errors."""

    def __init__(self, message: str, exit_code: int | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, cause)
        self.exit_code = exit_code


class AuthenticationError(ShakeNBakeError):
    """Git authentication errors."""

    pass


class ValidationError(ShakeNBakeError):
    """Data validation errors."""

    pass


class FileNotFoundError(ShakeNBakeError):
    """Required file not found errors."""

    pass


class TargetNotFoundError(ShakeNBakeError):
    """Build target not found errors."""

    pass
