"""Tests for core domain models."""

import json
import tempfile
from pathlib import Path

import pytest

from shake_n_bake.core.models import (
    BakeConfiguration,
    BakeContext,
    BuildOptions,
    BuildResult,
    BuildTarget,
    FileReference,
    ImageInfo,
    PathType,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary JSON configuration file for testing.

    Returns:
        A function that accepts configuration data and returns a Path to the temp file.
        The caller is responsible for cleaning up the file after use.

    Example:
        config_path = temp_config_file({"remote": "owner/repo#main", ...})
        try:
            # Use config_path
        finally:
            config_path.unlink()
    """

    def _create_config(data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            return Path(f.name)

    return _create_config


@pytest.fixture
def sample_config_data():
    """Sample configuration data matching the expected JSON format.

    This represents a realistic configuration with both remote and local files,
    using the JSON field names (pathDefinitions, filePath, isRemote) that would
    appear in actual __REQUIRED_BAKE_FILES.json files.
    """
    return {
        "remote": "owner/repo#main",
        "pathDefinitions": [
            {"filePath": "config/versions.hcl", "isRemote": True},
            {"filePath": "cwd://docker-bake.hcl", "isRemote": False},
        ],
    }


@pytest.fixture
def sample_images():
    """Sample ImageInfo objects representing typical build outputs.

    Includes both a simple image name and one with a registry to test
    various image name formats and metadata processing scenarios.
    """
    return [
        ImageInfo(name="myapp", tag="v1.0"),
        ImageInfo(name="utils", tag="latest", registry="ghcr.io"),
    ]


@pytest.fixture
def remote_file_ref():
    """FileReference for a remote Git repository file.

    Represents a typical remote file like config/versions.hcl that would
    be fetched from a Git repository during the build process.
    """
    return FileReference(file_path="config/versions.hcl", is_remote=True)


@pytest.fixture
def local_file_ref():
    """FileReference for a local file in the current working directory.

    Represents a local file like docker-bake.hcl that exists in the
    directory where the build is being executed.
    """
    return FileReference(file_path="cwd://docker-bake.hcl", is_remote=False)


@pytest.fixture
def remote_config(remote_file_ref, local_file_ref):
    """BakeConfiguration that requires Git authentication.

    Contains both remote and local file references, representing a typical
    setup where some configuration comes from a shared Git repository
    and some is local to the build directory.
    """
    return BakeConfiguration(remote="owner/repo#main", path_definitions=[remote_file_ref, local_file_ref])


@pytest.fixture
def local_config(local_file_ref):
    """BakeConfiguration with only local files (no Git auth needed).

    Represents a simple build setup where all configuration files
    exist locally in the build directory.
    """
    return BakeConfiguration(path_definitions=[local_file_ref])


@pytest.fixture
def successful_build_result(sample_images):
    """BuildResult representing a successful build operation.

    Includes realistic timing data and multiple output images,
    representing what would be returned after a successful
    Docker buildx bake execution.
    """
    return BuildResult(target="myapp", images=sample_images, success=True, duration_seconds=45.2)


class TestFileReference:
    """Tests for FileReference model.

    FileReference represents files that can be either:
    - Remote: Fetched from a Git repository (is_remote=True)
    - Local: Exist in the current working directory (is_remote=False)

    The path_type property automatically determines the type based on is_remote.
    """

    @pytest.mark.parametrize(
        "file_path,is_remote,expected_type",
        [
            ("config/versions.hcl", True, PathType.REMOTE),
            ("cwd://docker-bake.hcl", False, PathType.CWD),
            ("local-file.hcl", False, PathType.CWD),
        ],
    )
    def test_file_reference_types(self, file_path, is_remote, expected_type):
        """Test that path_type is correctly determined based on is_remote flag.

        The path_type should be REMOTE when is_remote=True regardless of file_path,
        and CWD when is_remote=False regardless of whether the path has cwd:// prefix.
        """
        ref = FileReference(file_path=file_path, is_remote=is_remote)

        assert ref.file_path == file_path
        assert ref.is_remote == is_remote
        assert ref.path_type == expected_type

    def test_empty_file_path_validation(self):
        """Test that empty file paths are rejected during validation.

        FileReference requires a non-empty file_path to be valid.
        """
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            FileReference(file_path="", is_remote=False)


class TestBakeConfiguration:
    """Tests for BakeConfiguration model."""

    def test_valid_configuration_with_remote(self, remote_config):
        """Test valid configuration with remote files."""
        assert remote_config.remote == "owner/repo#main"
        assert len(remote_config.path_definitions) == 2
        assert remote_config.has_remote_files is True

    def test_valid_configuration_without_remote(self, local_config):
        """Test valid configuration with only local files."""
        assert local_config.remote is None
        assert len(local_config.path_definitions) == 1
        assert local_config.has_remote_files is False

    def test_remote_files_without_remote_url_fails(self, remote_file_ref):
        """Test that remote files require a remote URL."""
        with pytest.raises(ValueError, match="Remote URL is required"):
            BakeConfiguration(path_definitions=[remote_file_ref])

    @pytest.mark.parametrize(
        "remote_value,expected",
        [
            ("   ", None),
            ("", None),
            ("  \t\n  ", None),
        ],
    )
    def test_empty_remote_url_normalized(self, remote_value, expected, local_file_ref):
        """Test that empty remote URL is normalized to None."""
        config = BakeConfiguration(remote=remote_value, path_definitions=[local_file_ref])
        assert config.remote == expected

    def test_from_file_success(self, temp_config_file, sample_config_data):
        """Test loading configuration from file."""
        config_path = temp_config_file(sample_config_data)

        try:
            config = BakeConfiguration.from_file(config_path)

            assert config.remote == "owner/repo#main"
            assert len(config.path_definitions) == 2
            assert config.path_definitions[0].file_path == "config/versions.hcl"
            assert config.path_definitions[0].is_remote is True
        finally:
            config_path.unlink()

    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(ValueError, match="Configuration file not found"):
            BakeConfiguration.from_file(Path("/nonexistent/path.json"))

    def test_from_file_invalid_json(self, temp_config_file):
        """Test loading from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                BakeConfiguration.from_file(temp_path)
        finally:
            temp_path.unlink()


class TestBuildOptions:
    """Tests for BuildOptions model."""

    def test_default_options(self):
        """Test default build options."""
        options = BuildOptions()

        assert options.metadata_file == "metadata.json"
        assert options.args == []
        assert options.to_args() == ["--metadata-file", "metadata.json"]

    @pytest.mark.parametrize(
        "metadata_file,args,expected",
        [
            ("custom.json", ["--no-cache"], ["--metadata-file", "custom.json", "--no-cache"]),
            ("build.json", ["--progress", "plain"], ["--metadata-file", "build.json", "--progress", "plain"]),
            ("meta.json", ["--no-cache", "--load"], ["--metadata-file", "meta.json", "--no-cache", "--load"]),
        ],
    )
    def test_custom_options(self, metadata_file, args, expected):
        """Test custom build options."""
        options = BuildOptions(metadata_file=metadata_file, args=args)
        assert options.to_args() == expected


class TestImageInfo:
    """Tests for ImageInfo model.

    ImageInfo represents Docker image metadata with proper registry parsing.
    The from_full_name() method implements Docker's official registry detection rules:
    - A component is considered a registry if it contains '.', ':', or equals 'localhost'
    - Registry ports (like localhost:5000) are correctly distinguished from image tags
    - All images must have explicit tags - no default 'latest' is assumed

    This parsing is critical for correctly handling various image name formats:
    - ubuntu:20.04 (Docker Hub, no registry)
    - ghcr.io/owner/repo:v1.0 (GitHub Container Registry)
    - localhost:5000/app:latest (Local registry with port)
    - company/team/app:latest (Multi-level namespace, no registry)
    """

    def test_image_properties(self):
        """Test basic image properties."""
        image = ImageInfo(name="ubuntu", tag="20.04")

        assert image.name == "ubuntu"
        assert image.tag == "20.04"
        assert image.registry is None
        assert image.full_name == "ubuntu:20.04"

    def test_image_with_registry(self):
        """Test image with registry."""
        image = ImageInfo(name="myapp", tag="latest", registry="ghcr.io")

        assert image.registry == "ghcr.io"
        assert image.full_name == "ghcr.io/myapp:latest"

    @pytest.mark.parametrize(
        "full_name,expected_name,expected_tag,expected_registry",
        [
            ("ubuntu:20.04", "ubuntu", "20.04", None),
            ("ghcr.io/owner/repo:v1.0", "owner/repo", "v1.0", "ghcr.io"),
            ("localhost:5000/myapp:latest", "myapp", "latest", "localhost:5000"),
            ("huloop/devcontainers/tools:latest", "huloop/devcontainers/tools", "latest", None),
            ("docker.io/library/postgres:13", "library/postgres", "13", "docker.io"),
            ("registry.example.com:8080/team/app:v2.1", "team/app", "v2.1", "registry.example.com:8080"),
        ],
    )
    def test_from_full_name_parsing(self, full_name, expected_name, expected_tag, expected_registry):
        """Test parsing various Docker image name formats according to Docker's rules.

        This test covers the key parsing scenarios:
        1. Simple Docker Hub images (ubuntu:20.04)
        2. Registry with domains containing dots (ghcr.io/...)
        3. Registry with ports (localhost:5000/...)
        4. Multi-level namespaces without registries (company/team/app:tag)
        5. Registry with both domain and port (registry.example.com:8080/...)

        The parsing logic correctly distinguishes between registry hostnames
        and image namespaces based on Docker's rules.
        """
        image = ImageInfo.from_full_name(full_name)

        assert image.name == expected_name
        assert image.tag == expected_tag
        assert image.registry == expected_registry

    @pytest.mark.parametrize(
        "invalid_name,error_pattern",
        [
            ("ubuntu", "Image name must include tag"),
            ("ubuntu:", "Tag cannot be empty"),
            ("ghcr.io/owner/repo", "Image name must include tag"),
            ("localhost:5000/app", "Image name must include tag"),
        ],
    )
    def test_from_full_name_validation_failures(self, invalid_name, error_pattern):
        """Test parsing failures for invalid image names."""
        with pytest.raises(ValueError, match=error_pattern):
            ImageInfo.from_full_name(invalid_name)


class TestBuildResult:
    """Tests for BuildResult model."""

    def test_successful_build_result(self, successful_build_result):
        """Test successful build result."""
        assert successful_build_result.target == "myapp"
        assert len(successful_build_result.images) == 2
        assert successful_build_result.success is True
        assert successful_build_result.duration_seconds == 45.2
        assert successful_build_result.error_message is None

    @pytest.mark.parametrize(
        "target,error_msg",
        [
            ("api", "Connection timeout"),
            ("web", "Build failed due to missing dependency"),
            ("worker", "Out of disk space"),
        ],
    )
    def test_failed_build_result(self, target, error_msg):
        """Test failed build result."""
        result = BuildResult(target=target, success=False, error_message=error_msg)

        assert result.target == target
        assert result.success is False
        assert result.error_message == error_msg
        assert result.images == []


class TestBuildTarget:
    """Tests for BuildTarget model."""

    def test_valid_target(self):
        """Test valid build target."""
        target = BuildTarget(name="api", description="API service")

        assert target.name == "api"
        assert target.description == "API service"

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            "   ",
            "\t\n",
        ],
    )
    def test_empty_target_name_validation(self, invalid_name):
        """Test validation of empty target names."""
        with pytest.raises(ValueError, match="Target name cannot be empty"):
            BuildTarget(name=invalid_name)


class TestBakeContext:
    """Tests for BakeContext model."""

    def test_bake_context_properties(self, remote_config):
        """Test BakeContext properties."""
        context = BakeContext(directory=Path("/test/dir"), configuration=remote_config, target="api")

        assert context.config_file_path == Path("/test/dir/__REQUIRED_BAKE_FILES.json")
        assert context.requires_git_auth is True

    def test_bake_context_no_git_auth(self, local_config):
        """Test BakeContext with no git auth needed."""
        context = BakeContext(directory=Path("/test/dir"), configuration=local_config)

        assert context.requires_git_auth is False


class TestBakeConfigurationEdgeCases:
    """Test edge cases for BakeConfiguration."""

    def test_from_file_generic_exception(self, temp_config_file):
        """Test generic exception handling in from_file."""
        # Create a config that will cause a validation error
        invalid_config = {
            "remote": "owner/repo#main",
            "path_definitions": "not_a_list",  # This should be a list
        }

        config_path = temp_config_file(invalid_config)

        try:
            with pytest.raises(ValueError, match="Failed to load configuration"):
                BakeConfiguration.from_file(config_path)
        finally:
            config_path.unlink()
