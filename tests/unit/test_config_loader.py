"""Tests for configuration loading and validation.

The configuration layer handles:
- Loading BakeConfiguration from JSON files
- Validating directory structure and permissions
- Creating BakeContext objects that combine configuration with runtime parameters
- Building docker buildx bake command arguments from configuration

Testing Strategy:
- Mock filesystem operations where appropriate
- Use temporary directories and files for integration testing
- Test both successful and failure scenarios
- Validate error messages and exception types
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from shake_n_bake.config.loader import (
    ConfigurationLoader,
    Settings,
    get_bake_file_args,
    settings,
)
from shake_n_bake.core.constants import REQUIRED_BAKE_FILES
from shake_n_bake.core.exceptions import ConfigurationError, FileNotFoundError
from shake_n_bake.core.models import BakeConfiguration, BakeContext, FileReference


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def config_loader():
    """ConfigurationLoader with default settings."""
    return ConfigurationLoader()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Mock(spec=Settings, is_ci=False, git_auth_token=None, git_ssh_socket=None)


@pytest.fixture
def sample_config_json():
    """Sample configuration JSON data."""
    return {
        "remote": "owner/repo#main",
        "pathDefinitions": [
            {"filePath": "config/versions.hcl", "isRemote": True},
            {"filePath": "cwd://docker-bake.hcl", "isRemote": False},
        ],
    }


@pytest.fixture
def config_file(temp_dir, sample_config_json):
    """Create a temporary config file."""
    config_path = temp_dir / REQUIRED_BAKE_FILES
    with open(config_path, "w") as f:
        json.dump(sample_config_json, f)
    return config_path


class TestSettings:
    """Tests for Settings configuration model."""

    def test_default_settings(self):
        """Test default settings values."""
        settings_obj = Settings()

        assert settings_obj.log_level == "INFO"
        assert settings_obj.debug is False
        assert settings_obj.buildx_entitlements_fs == "0"

    @patch.dict(os.environ, {"CI": "true", "BUILDX_BAKE_GIT_AUTH_TOKEN": "test-token"})
    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        settings_obj = Settings()

        assert settings_obj.is_ci is True
        assert settings_obj.git_auth_token == "test-token"

    def test_configure_environment(self):
        """Test environment configuration."""
        settings_obj = Settings()

        with patch.dict(os.environ, {}, clear=True):
            settings_obj.configure_environment()

            assert os.environ["BUILDX_BAKE_ENTITLEMENTS_FS"] == "0"


class TestConfigurationLoader:
    """Tests for ConfigurationLoader class."""

    def test_validate_directory_success(self, config_loader, temp_dir):
        """Test successful directory validation."""
        # Should not raise any exception
        config_loader._validate_directory(temp_dir)

    def test_validate_directory_not_exists(self, config_loader):
        """Test validation fails for non-existent directory."""
        non_existent = Path("/this/does/not/exist")

        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            config_loader._validate_directory(non_existent)

    def test_validate_directory_not_directory(self, config_loader, temp_dir):
        """Test validation fails when path is a file, not directory."""
        file_path = temp_dir / "not_a_directory.txt"
        file_path.write_text("content")

        with pytest.raises(ConfigurationError, match="Path is not a directory"):
            config_loader._validate_directory(file_path)

    @patch("os.access")
    def test_validate_directory_not_readable(self, mock_access, config_loader, temp_dir):
        """Test validation fails when directory is not readable."""
        mock_access.return_value = False

        with pytest.raises(ConfigurationError, match="Cannot read directory"):
            config_loader._validate_directory(temp_dir)

    def test_load_configuration_success(self, config_loader, config_file):
        """Test successful configuration loading."""
        config_dir = config_file.parent

        config = config_loader._load_configuration(config_dir)

        assert isinstance(config, BakeConfiguration)
        assert config.remote == "owner/repo#main"
        assert len(config.path_definitions) == 2
        assert config.has_remote_files is True

    def test_load_configuration_file_not_found(self, config_loader, temp_dir):
        """Test loading fails when config file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Required configuration file not found"):
            config_loader._load_configuration(temp_dir)

    def test_load_configuration_invalid_json(self, config_loader, temp_dir):
        """Test loading fails with invalid JSON."""
        config_path = temp_dir / REQUIRED_BAKE_FILES
        config_path.write_text("{ invalid json }")

        with pytest.raises(ConfigurationError, match="Failed to load configuration"):
            config_loader._load_configuration(temp_dir)

    def test_create_context(self, config_loader, temp_dir):
        """Test BakeContext creation."""
        config = BakeConfiguration(
            remote="owner/repo#main", path_definitions=[FileReference(file_path="config/versions.hcl", is_remote=True)]
        )

        context = config_loader._create_context(
            directory=temp_dir, configuration=config, target="api", bake_args=["--no-cache"]
        )

        assert isinstance(context, BakeContext)
        assert context.directory == temp_dir.resolve()
        assert context.configuration == config
        assert context.target == "api"
        assert context.options.args == ["--no-cache"]

    def test_load_bake_context_integration(self, config_loader, config_file):
        """Test complete bake context loading workflow."""
        config_dir = config_file.parent

        context = config_loader.load_bake_context(directory=config_dir, target="api", bake_args=["--progress", "plain"])

        assert isinstance(context, BakeContext)
        assert context.directory == config_dir.resolve()
        assert context.target == "api"
        assert context.options.args == ["--progress", "plain"]
        assert context.requires_git_auth is True

    def test_load_bake_context_no_target(self, config_loader, config_file):
        """Test loading context without specifying target."""
        config_dir = config_file.parent

        context = config_loader.load_bake_context(directory=config_dir)

        assert context.target is None
        assert context.options.args == []

    def test_validate_context_with_git_auth(self, config_loader, mock_settings):
        """Test context validation when Git auth is required."""
        mock_settings.is_ci = False
        mock_settings.git_auth_token = None
        config_loader.settings = mock_settings

        config = BakeConfiguration(
            remote="owner/repo#main", path_definitions=[FileReference(file_path="config/versions.hcl", is_remote=True)]
        )
        context = BakeContext(directory=Path("/test"), configuration=config, target="api")

        # Should not raise exception, but might log warning
        with patch("os.access", return_value=True):
            config_loader.validate_context(context)

    @patch("os.access")
    def test_validate_context_not_writable(self, mock_access, config_loader, mock_settings):
        """Test context validation when directory is not writable."""
        mock_access.side_effect = lambda path, mode: mode != os.W_OK
        config_loader.settings = mock_settings

        config = BakeConfiguration(path_definitions=[FileReference(file_path="cwd://docker-bake.hcl", is_remote=False)])
        context = BakeContext(directory=Path("/test"), configuration=config)

        # Should not raise exception, but might log warning
        config_loader.validate_context(context)


class TestGetBakeFileArgs:
    """Tests for get_bake_file_args utility function."""

    def test_local_files_only(self):
        """Test bake file args for local-only configuration."""
        config = BakeConfiguration(
            path_definitions=[
                FileReference(file_path="cwd://docker-bake.hcl", is_remote=False),
                FileReference(file_path="local-compose.yml", is_remote=False),
            ]
        )

        args = get_bake_file_args(config)

        expected = ["--file", "cwd://docker-bake.hcl", "--file", "local-compose.yml"]
        assert args == expected

    def test_remote_files_included(self):
        """Test bake file args includes remote repository."""
        config = BakeConfiguration(
            remote="owner/repo#main",
            path_definitions=[
                FileReference(file_path="config/versions.hcl", is_remote=True),
                FileReference(file_path="cwd://docker-bake.hcl", is_remote=False),
            ],
        )

        args = get_bake_file_args(config)

        expected = ["--file", "owner/repo#main", "--file", "config/versions.hcl", "--file", "cwd://docker-bake.hcl"]
        assert args == expected

    @pytest.mark.parametrize(
        "remote,path_defs,expected",
        [
            (None, [], "List should have at least 1 item"),
            ("owner/repo#main", [], "List should have at least 1 item"),
            (
                None,
                [FileReference(file_path="config/versions.hcl", is_remote=True)],
                "Remote URL is required when path_definitions contain remote references",
            ),
        ],
    )
    def test_empty_configuration(self, remote, path_defs, expected):
        """Test bake file args with empty configuration."""
        with pytest.raises(ValidationError, match=expected):
            BakeConfiguration(remote=remote, path_definitions=path_defs)


class TestGlobalSettings:
    """Tests for global settings instance."""

    def test_global_settings_exists(self):
        """Test that global settings instance is accessible."""
        assert settings is not None
        assert isinstance(settings, Settings)
