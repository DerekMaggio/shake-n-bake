"""Constants used throughout shake-n-bake."""

# Configuration files
REQUIRED_BAKE_FILES = "__REQUIRED_BAKE_FILES.json"
DEFAULT_METADATA_FILE = "metadata.json"

# Environment variables
CI_ENV_VAR = "CI"
GIT_AUTH_TOKEN_VAR = "BUILDX_BAKE_GIT_AUTH_TOKEN"
GIT_SSH_SOCKET_VAR = "BUILDX_BAKE_GIT_SSH"

# Docker buildx settings
BUILDX_ENTITLEMENTS_FS = "BUILDX_BAKE_ENTITLEMENTS_FS"
DEFAULT_BUILDX_ENTITLEMENTS_FS = "0"

# Git authentication
DEFAULT_GIT_SSH_SOCKET = "/tmp/ssh-agent.sock"
GITHUB_HOSTNAME = "github.com"

# Default values
DEFAULT_TAG = "latest"
DEFAULT_PROGRESS = "auto"

# File patterns
CWD_PREFIX = "cwd://"
DOCKER_HUB_REGISTRY = "docker.io"
