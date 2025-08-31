"""Docker buildx bake execution."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, cast

import structlog
from invoke import Context
from rich.console import Console

from ..config.loader import get_bake_file_args
from ..core.constants import BUILDX_ENTITLEMENTS_FS, DEFAULT_BUILDX_ENTITLEMENTS_FS
from ..core.exceptions import DockerError
from ..core.models import BakeContext, BuildResult, ImageInfo

logger = structlog.get_logger(__name__)
console = Console()


class DockerBakeExecutor:
    """Executes Docker buildx bake operations."""

    def __init__(self, context: Context | None = None) -> None:
        self.ctx = context or Context()
        self._configure_environment()

    def _configure_environment(self) -> None:
        """Configure environment variables for Docker buildx."""
        self.ctx.config.run.env[BUILDX_ENTITLEMENTS_FS] = DEFAULT_BUILDX_ENTITLEMENTS_FS
        logger.debug("Docker environment configured")

    def get_targets(self, bake_context: BakeContext) -> List[str]:
        """Get available build targets from bake files."""
        logger.info("Discovering build targets", directory=str(bake_context.directory))

        bake_args = get_bake_file_args(bake_context.configuration)
        cmd_parts = ["docker", "buildx", "bake"] + bake_args + ["--list-targets"]
        cmd = " ".join(cmd_parts)

        try:
            with console.status("Getting build targets..."):
                result = self.ctx.run(cmd, hide=True, warn=True, cwd=str(bake_context.directory))

            if result.failed:
                raise DockerError(f"Failed to get build targets: {result.stderr}", exit_code=result.return_code)

            targets = self._parse_targets_output(result.stdout)
            logger.info("Found build targets", targets=targets, count=len(targets))
            return targets

        except Exception as e:
            if isinstance(e, DockerError):
                raise
            raise DockerError(f"Error discovering build targets: {e}") from e

    def _parse_targets_output(self, output: str) -> List[str]:
        """Parse build targets from docker buildx bake --list-targets output."""
        targets = []

        for line in output.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("TARGET"):
                target = line.split()[0]
                if target:
                    targets.append(target)

        return targets

    def _build_command(self, bake_context: BakeContext) -> str:
        """Build the docker buildx bake command."""
        bake_args = get_bake_file_args(bake_context.configuration)
        build_args = bake_context.options.to_args()

        cmd_parts = ["docker", "buildx", "bake"] + bake_args + build_args + [bake_context.target]
        return " ".join(cmd for cmd in cmd_parts if cmd is not None)

    def _run_bake_command(self, cmd: str, working_dir: Path) -> None:
        """Execute the docker buildx bake command."""
        logger.debug("Executing docker command", cmd=cmd)

        result = self.ctx.run(cmd, warn=True, cwd=str(working_dir))

        if result.failed:
            raise DockerError(f"Docker bake failed: {result.stderr}", exit_code=result.return_code)

    def _create_build_result(
        self, bake_context: BakeContext, duration: float, success: bool, error: str | None = None
    ) -> BuildResult:
        """Create a BuildResult from execution results."""
        assert bake_context.target is not None
        if success:
            metadata = self._load_build_metadata(bake_context)
            images = self._extract_images_from_metadata(metadata)
            return BuildResult(
                target=bake_context.target,
                images=images,
                success=True,
                duration_seconds=duration,
                metadata=metadata,
            )
        else:
            return BuildResult(
                target=bake_context.target,
                success=False,
                duration_seconds=duration,
                error_message=error,
            )

    def execute_bake(self, bake_context: BakeContext) -> BuildResult:
        """Execute docker buildx bake command."""
        if not bake_context.target:
            raise ValueError("Target must be specified for bake execution")

        logger.info("Starting bake execution", target=bake_context.target)

        start_time = time.time()

        try:
            cmd = self._build_command(bake_context)

            with console.status(f"Building {bake_context.target}..."):
                self._run_bake_command(cmd, bake_context.directory)

            duration = time.time() - start_time
            result = self._create_build_result(bake_context, duration, success=True)

            logger.info("Bake execution completed", target=bake_context.target, duration=f"{duration:.2f}s")
            return result

        except Exception as e:
            duration = time.time() - start_time
            result = self._create_build_result(bake_context, duration, success=False, error=str(e))

            logger.error("Bake execution failed", target=bake_context.target, error=str(e))
            return result

    # we don't build the metadata object so we don't need to type it strictly here
    def _load_build_metadata(self, bake_context: BakeContext) -> Dict[str, Any]:
        """Load build metadata from metadata file."""
        metadata_file = bake_context.directory / bake_context.options.metadata_file

        if not metadata_file.exists():
            logger.warning("Metadata file not found", file=str(metadata_file))
            return {}

        try:
            with open(metadata_file) as f:
                return cast(Dict[str, Any], json.load(f))
        except Exception as e:
            logger.warning("Failed to load metadata", file=str(metadata_file), error=str(e))
            return {}

    def _extract_images_from_metadata(self, metadata: Dict[str, Any]) -> List[ImageInfo]:
        """Extract image information from build metadata."""
        images = []

        try:
            for _, target_data in metadata.items():
                image_names = target_data.get("image.name", "")

                if not image_names:
                    continue

                for image_name in image_names.split(","):
                    image_name = image_name.strip()
                    if image_name:
                        try:
                            image_info = ImageInfo.from_full_name(image_name)
                            images.append(image_info)
                        except ValueError as e:
                            logger.warning("Failed to parse image name", image=image_name, error=str(e))

        except Exception as e:
            logger.warning("Failed to extract images from metadata", error=str(e))

        return images
