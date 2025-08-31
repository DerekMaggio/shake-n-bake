"""Core domain models for shake-n-bake."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class PathType(str, Enum):
    """Type of file path reference."""

    REMOTE = "remote"
    CWD = "cwd"


class FileReference(BaseModel):
    """Represents a file that can be remote or relative to CWD."""

    file_path: str = Field(..., description="Path to the file")
    is_remote: bool = Field(..., description="Whether the file is from a remote repository")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path format."""
        if not v:
            raise ValueError("file_path cannot be empty")
        return v

    @property
    def path_type(self) -> PathType:
        """Get the path type based on is_remote flag."""
        return PathType.REMOTE if self.is_remote else PathType.CWD


class BakeConfiguration(BaseModel):
    """Configuration for a bake operation."""

    remote: Optional[str] = Field(default=None, description="Remote repository URL")
    path_definitions: List[FileReference] = Field(
        default_factory=list, description="List of file references for the bake", min_length=1
    )

    @field_validator("remote")
    @classmethod
    def validate_remote_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize remote repository reference."""
        if v is not None:
            v = v.strip()
            if v == "":
                return None
            # GitPython will handle validation of the actual repository reference
        return v

    @property
    def has_remote_files(self) -> bool:
        """Check if configuration uses remote files."""
        return any(ref.is_remote for ref in self.path_definitions)

    @model_validator(mode="after")
    def validate_remote_consistency(self) -> BakeConfiguration:
        """Ensure remote is provided when remote paths exist."""
        if self.has_remote_files and not self.remote:
            raise ValueError("Remote URL is required when path_definitions contain remote references")
        return self

    @classmethod
    def from_file(cls, config_path: Path) -> BakeConfiguration:
        """Load configuration from JSON file."""
        try:
            with open(config_path, "r") as f:
                data = json.load(f)

            # Convert pathDefinitions to path_definitions for Python naming
            if "pathDefinitions" in data:
                path_definitions = []
                for path_def in data["pathDefinitions"]:
                    # Convert JSON field names to Python field names
                    converted = {"file_path": path_def["filePath"], "is_remote": path_def["isRemote"]}
                    path_definitions.append(converted)
                data["path_definitions"] = path_definitions
                data.pop("pathDefinitions")

            return cls.model_validate(data)

        except FileNotFoundError as e:
            raise ValueError(f"Configuration file not found: {config_path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}") from e


class BuildTarget(BaseModel):
    """Represents a Docker build target."""

    name: str = Field(..., description="Name of the build target")
    description: Optional[str] = Field(default=None, description="Description of what this target builds")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate target name."""
        if not v or not v.strip():
            raise ValueError("Target name cannot be empty")
        return v.strip()


class BuildOptions(BaseModel):
    """Options for Docker buildx bake command."""

    metadata_file: str = Field(default="metadata.json", description="Path to write build metadata")
    args: List[str] = Field(default_factory=list, description="Arguments to pass to buildx bake")

    def to_args(self) -> List[str]:
        """Convert options to command line arguments."""
        result = ["--metadata-file", self.metadata_file]
        result.extend(self.args)
        return result


class ImageInfo(BaseModel):
    """Information about a built Docker image."""

    name: str = Field(..., description="Image name")
    tag: str = Field(..., description="Image tag")
    registry: Optional[str] = Field(default=None, description="Registry where image is stored")

    @property
    def full_name(self) -> str:
        """Get the full image name including registry."""
        if self.registry:
            return f"{self.registry}/{self.name}:{self.tag}"
        return f"{self.name}:{self.tag}"

    @classmethod
    def from_full_name(cls, full_name: str) -> ImageInfo:
        """Create ImageInfo from full image name using Docker's parsing rules.

        Registry detection follows Docker's official logic:
        https://stackoverflow.com/questions/37861791/how-are-docker-image-names-parsed
        A component is a registry if it contains '.', ':', or equals 'localhost'

        Note: Tag must be explicitly specified - no default tag is assumed.
        """
        # Split tag - but be careful not to split on registry port numbers
        # Only treat the part after the last colon as a tag if there's no slash after it
        if ":" not in full_name:
            raise ValueError(f"Image name must include tag: {full_name}")

        # Find the last colon and check if it's followed by a slash (indicating registry port)
        last_colon_idx = full_name.rfind(":")
        potential_tag = full_name[last_colon_idx + 1 :]

        # If there's a slash in the potential tag, it's actually part of a registry hostname
        if "/" in potential_tag:
            raise ValueError(f"Image name must include tag: {full_name}")

        name_part = full_name[:last_colon_idx]
        tag = potential_tag

        if not tag:
            raise ValueError(f"Tag cannot be empty: {full_name}")

        # Check if there's a registry using Docker's rules
        if "/" in name_part:
            # Get the first component before the first slash
            first_slash = name_part.find("/")
            potential_registry = name_part[:first_slash]

            # Docker's rule: registry if it contains '.', ':', or is 'localhost'
            is_registry = "." in potential_registry or ":" in potential_registry or potential_registry == "localhost"

            if is_registry:
                registry = potential_registry
                name = name_part[first_slash + 1 :]
                return cls(name=name, tag=tag, registry=registry)

        # No registry found, treat entire name_part as image name
        return cls(name=name_part, tag=tag)


class BuildResult(BaseModel):
    """Result of a build operation."""

    target: str = Field(..., description="Target that was built")
    images: List[ImageInfo] = Field(default_factory=list, description="Images produced by the build")
    success: bool = Field(..., description="Whether the build succeeded")
    duration_seconds: Optional[float] = Field(default=None, description="Build duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional build metadata")
    error_message: Optional[str] = Field(default=None, description="Error message if build failed")


class BakeContext(BaseModel):
    """Context for a bake operation."""

    directory: Path = Field(..., description="Directory containing the bake configuration")
    configuration: BakeConfiguration = Field(..., description="Bake configuration")
    target: Optional[str] = Field(default=None, description="Specific target to build")
    options: BuildOptions = Field(default_factory=BuildOptions, description="Build options")

    @property
    def config_file_path(self) -> Path:
        """Path to the configuration file."""
        return self.directory / "__REQUIRED_BAKE_FILES.json"

    @property
    def requires_git_auth(self) -> bool:
        """Whether this bake requires Git authentication."""
        return self.configuration.has_remote_files
