#!/bin/bash

set -e

trap 'cd "$CURRENT_DIR"; exit 1' ERR
trap 'cd "$CURRENT_DIR"' EXIT

function usage_dir() {
    echo
    echo "Usage: $(basename ${0}) DIR TARGET [BAKE OPTIONS]"
    echo
    usage_examples "DIR"
}

function usage_examples() {
    local dir="$1"

    echo "Examples:"
    echo "  Normal execution:"
    echo "  $(basename ${0}) ${dir} TARGET"
    echo
    echo "  Show all progress:"
    echo "  $(basename ${0}) ${dir} TARGET --progress plain"
    echo
    echo "  No cache:"
    echo "  $(basename ${0}) ${dir} TARGET --no-cache"
}

function usage_empty_target() {
    local dir="$1"
    cd "${dir}" || exit 1
    echo
    echo "ERROR: Please specify a target."
    echo 
    echo "Usage: $(basename ${0}) ${dir} TARGET [BAKE OPTIONS]"
    echo 
    echo "Getting targets..."
    echo
    local bake_files=$(build_bake_file_options "${dir}/${REQUIRED_BAKE_FILES_FILE_NAME}")
    bash -c "docker buildx bake ${bake_files} --progress plain --list targets"
    echo 
    usage_examples "${dir}"
    echo
    echo "##################################"
    echo "#  Shakin' and bakin' failed :(  #"
    echo "##################################"
    echo
    cd "${CURRENT_DIR}" || exit 1
}


function setup_gh_auth_local() {
    export BUILDX_BAKE_GIT_AUTH_TOKEN=$(gh auth token)

    if [ -z "$BUILDX_BAKE_GIT_AUTH_TOKEN" ]; then
        gh auth login \
            --git-protocol https \
            --hostname github.com \
            --web \
            --scopes "read:packages"
        export BUILDX_BAKE_GIT_AUTH_TOKEN=$(gh auth token)
    fi
    
    local gh_username=$(gh api user -q '.login')
    gh auth token | docker login ghcr.io --username "${gh_username}" --password-stdin
}

function git_auth_needed() {
    local file_path="${1}"
    # Always return "true" or "false" even if pathDefinitions is empty or missing
    cat "${file_path}" | jq -r '
        (any(.pathDefinitions[]?; .isRemote == true) and (.remote != null and .remote != "")) // false
        | if . then "true" else "false" end'
}

function build_bake_file_options() {
    local file_path="${1}"

    # Check for isRemote true but remote is blank/null
    local has_remote=$(cat "${file_path}" | jq -r '[.pathDefinitions[] | select(.isRemote == true)] | length')
    local remote=$(cat "${file_path}" | jq -r '.remote // ""')
    if [ "$has_remote" -gt 0 ] && [ -z "$remote" ]; then
        echo "ERROR: At least one pathDefinition has isRemote=true, but top-level 'remote' is blank or missing in ${file_path}." >&2
        exit 1
    fi

    jq_script='
        def ensure_prefix($ci; $remote):
            if $remote == "" then null
            else
                if $ci == "true" then
                    "git@github.com:" + $remote
                else
                    "https://github.com/" + $remote
                end
            end;
        . as $root |
        (
            if ($root.pathDefinitions | map(.isRemote == true) | any) and ($root.remote != null and $root.remote != "")
            then [ensure_prefix($ci; $root.remote)]
            else []
            end
        ) +
        ($root.pathDefinitions | map("--file \"" + .filePath + "\""))
        | join(" ")
    '

    cat "${file_path}" | jq -r --arg ci "${CI}" --arg remote "$remote" "${jq_script}"
}

function required_bake_files_error() {
    local dir="${1}"
    echo
    echo "ERROR: No \"${REQUIRED_BAKE_FILES_FILE_NAME}\" file found in \"${dir}\"."
    echo "Please create a file named \"${REQUIRED_BAKE_FILES_FILE_NAME}\" in the directory."
    echo 
    echo "Example content:"
    cat << EOF
{
    "remote": "https://github.com/AgreeYa-HuLoop/huloop-dev-tools.git",
    "pathDefinitions": [
        {
            "isRemote": true,
            "filePath": "config/versions.hcl"
        },
        {
            "isRemote": true,
            "filePath": "config/user.hcl"
        },
        {
            "isRemote": false,
            "filePath": "cwd://docker-bake.hcl"
        }
    ]
}
EOF
    echo
    exit 1
}

function bake() {
    local folder="${1}"
    local target="${2}"
    
    local bake_files=$(build_bake_file_options "${folder}/${REQUIRED_BAKE_FILES_FILE_NAME}")
    local status=$?
    if [ $status -ne 0 ]; then
        echo "Aborting due to previous error."
        exit $status
    fi

    echo "Baking in folder: ${folder}"
    echo "Target: ${target}"
    echo "Options: ${BAKE_OPTIONS[*]}"
    echo "Bake files: ${bake_files[*]}"
    echo
    
    local metadata_file="metadata.json"
    local bake_options=""

    if [ "${BAKE_OPTIONS[*]}" ]; then
        local bake_options="${BAKE_OPTIONS[*]}"
    fi

    CMD_STRING="${bake_files} --metadata-file ${metadata_file} ${bake_options} \"${target}\""

    echo "Running command: docker buildx bake ${CMD_STRING}"
    bash -c "docker buildx bake ${CMD_STRING}"

    status=$?
    if [ $status -ne 0 ]; then
        echo "docker buildx bake failed with status $status"
        exit $status
    fi

    local filename_base=$(basename "${folder}_built_images")
    local json_filename="${filename_base}.json"

    cat "${metadata_file}" \
    | jq -r '
    to_entries
    | map(.value["image.name"])
    | map(select(. != null and . != ""))
    | if length == 0 then
        "{}"
      else
        map(split(","))
        | flatten
        | map(capture("(?<name>.+):(?<tag>.+)"))
        | map(.name |= sub("^(docker\\.io/)";""))
        | group_by(.name)
        | map({ (.[0].name): map(.tag) })
        | add
      end
    ' > "${folder}/${json_filename}"
}

export BUILDX_BAKE_ENTITLEMENTS_FS=0

if [[ " $* " == *" --help "* || " $* " == *" -h "* ]]; then
    usage_dir
    exit 0
fi

DIR="$(realpath -m "${1}")"
TARGET="${2}"
shift 2 || true
BAKE_OPTIONS=("$@")

CURRENT_DIR="$(pwd)"
REQUIRED_BAKE_FILES_FILE_NAME="__REQUIRED_BAKE_FILES.json"

if [ -z "${DIR}" ]; then
    echo
    usage_dir
    exit 1
fi

if [ ! -d "${DIR}" ]; then
    echo
    echo "ERROR: Directory \"${DIR}\" does not exist."
    usage_dir
    exit 1
fi

if [ ! -f "${DIR}/${REQUIRED_BAKE_FILES_FILE_NAME}" ]; then
    required_bake_files_error "${DIR}"
fi

if [ "$(git_auth_needed "${DIR}/${REQUIRED_BAKE_FILES_FILE_NAME}")" == "true" ]; then
    echo "Git authentication is needed for the bake process."
    if [ "${CI}" != "true" ]; then
        echo "Setting up GitHub authentication locally..."
        setup_gh_auth_local
    else
        echo "Setting up GitHub authentication in CI..."
        export BUILDX_BAKE_GIT_SSH="/tmp/ssh-agent.sock"
    fi

    
fi

if [ -z "${TARGET}" ]; then
    usage_empty_target "${DIR}"
    exit 1
fi



cd "${DIR}" || exit 1
bake "${DIR}" "${TARGET}"
cd "${CURRENT_DIR}" || exit 1

