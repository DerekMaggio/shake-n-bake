"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import List

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..core.constants import (
    BUILDX_ENTITLEMENTS_FS,
    CI_ENV_VAR,
    DEFAULT_BUILDX_ENTITLEMENTS_FS,
    GIT_AUTH_TOKEN_VAR,
    GIT_SSH_SOCKET_VAR,
    REQUIRED_BAKE_FILES,
)
from ..core.exceptions import ConfigurationError, FileNotFoundError
from ..core.models import BakeConfiguration, BakeContext, BuildOptions

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="SHAKE_N_BAKE_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Logging
    log_level: str = "INFO"
    debug: bool = False

    # Docker settings
    buildx_entitlements_fs: str = DEFAULT_BUILDX_ENTITLEMENTS_FS

    # Git authentication
    git_auth_token: str | None = None
    git_ssh_socket: str | None = None

    # CI detection
    is_ci: bool = False

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        # Load CI status from environment
        self.is_ci = os.getenv(CI_ENV_VAR, "").lower() == "true"
        # Load git auth settings from environment
        self.git_auth_token = os.getenv(GIT_AUTH_TOKEN_VAR)
        self.git_ssh_socket = os.getenv(GIT_SSH_SOCKET_VAR)

    def configure_environment(self) -> None:
        """Configure environment variables for Docker buildx."""
        os.environ[BUILDX_ENTITLEMENTS_FS] = self.buildx_entitlements_fs

        if self.git_auth_token:
            os.environ[GIT_AUTH_TOKEN_VAR] = self.git_auth_token

        if self.git_ssh_socket:
            os.environ[GIT_SSH_SOCKET_VAR] = self.git_ssh_socket

        logger.debug(
            "Environment configured",
            buildx_entitlements_fs=self.buildx_entitlements_fs,
            has_git_token=bool(self.git_auth_token),
            has_git_ssh=bool(self.git_ssh_socket),
            is_ci=self.is_ci,
        )


class ConfigurationLoader:
    """Loads and validates bake configurations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def _validate_directory(self, directory: Path) -> None:
        """Validate that directory exists and is accessible."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise ConfigurationError(f"Path is not a directory: {directory}")

        if not os.access(directory, os.R_OK):
            raise ConfigurationError(f"Cannot read directory: {directory}")

    def _load_configuration(self, directory: Path) -> BakeConfiguration:
        """Load bake configuration from directory."""
        config_path = directory / REQUIRED_BAKE_FILES

        if not config_path.exists():
            raise FileNotFoundError(
                f"Required configuration file not found: {config_path}\\n"
                f"Please create a '{REQUIRED_BAKE_FILES}' file in the directory."
            )

        try:
            return BakeConfiguration.from_file(config_path)
        except ValueError as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _create_context(
        self,
        directory: Path,
        configuration: BakeConfiguration,
        target: str | None,
        bake_args: List[str],
    ) -> BakeContext:
        """Create bake context from components."""
        options = BuildOptions(args=bake_args)

        return BakeContext(
            directory=directory.resolve(),
            configuration=configuration,
            target=target,
            options=options,
        )

    def load_bake_context(
        self,
        directory: Path,
        target: str | None = None,
        bake_args: List[str] | None = None,
    ) -> BakeContext:
        """Load a complete bake context from a directory."""
        logger.info("Loading bake context", directory=str(directory), target=target)

        self._validate_directory(directory)
        configuration = self._load_configuration(directory)
        context = self._create_context(directory, configuration, target, bake_args or [])

        logger.debug(
            "Bake context loaded",
            has_remote_files=context.requires_git_auth,
            num_path_definitions=len(configuration.path_definitions),
            target=target,
        )

        return context

    def validate_context(self, context: BakeContext) -> None:
        """Validate that a bake context is ready for execution."""
        logger.debug("Validating bake context")

        # Check git authentication requirements
        if context.requires_git_auth:
            if not self.settings.is_ci and not self.settings.git_auth_token:
                logger.warning(
                    "Git authentication may be required but no token found. Run authentication setup if builds fail."
                )

        # Check directory write access for metadata
        if not os.access(context.directory, os.W_OK):
            logger.warning(
                "Directory is not writable, metadata file may fail to write", directory=str(context.directory)
            )

        logger.debug("Bake context validation completed")


def get_bake_file_args(configuration: BakeConfiguration) -> List[str]:
    """Build the --file arguments for docker buildx bake from configuration."""
    args: List[str] = []

    # Add remote repository reference if needed
    # GitPython and Docker buildx will handle the Git URL resolution
    if configuration.has_remote_files and configuration.remote:
        args.extend(["--file", configuration.remote])

    # Add individual file references
    for ref in configuration.path_definitions:
        args.extend(["--file", ref.file_path])

    logger.debug("Built bake file arguments", args=args)
    return args


# Global settings instance
settings = Settings()
