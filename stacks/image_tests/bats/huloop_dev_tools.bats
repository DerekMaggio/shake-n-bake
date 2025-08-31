#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(USER_HOME TERRAFORM_VERSION MONGOSH_VERSION MONGO_TOOLS_VERSION)

setup_file() {
    local MISSING_ENV_VARS=()
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_ENV_VARS+=("$var")
        fi
    done

    if [ ${#MISSING_ENV_VARS[@]} -ne 0 ]; then
        echo "The following environment variables are not set: ${MISSING_ENV_VARS[*]}"
        echo "Please set them before running the tests."
        exit 1
    fi
}

@test "az is installed" {
    az --version
}

@test "gh is installed" {
    gh --version
}

@test "sudo works" {
    run sudo echo "Sudo is working"
    [ "$status" -eq 0 ]
}

@test "shake-n-bake installed" {
    run shake-n-bake --help
    [ "$status" -eq 0 ]
}

@test "bash_aliases file exists" {
    assert_file_exists "${USER_HOME}/.bash_aliases"
}

@test "terraform is installed and version is ${TERRAFORM_VERSION}" {
    run bats_pipe terraform -version -json \| jq -r '.terraform_version'
    [ "$status" -eq 0 ]
    [[ "$output" == "${TERRAFORM_VERSION}" ]]
}

@test "mongosh is installed and version is ${MONGOSH_VERSION}" {
    run mongosh --version
    [ "$status" -eq 0 ]
    [[ "$output" == "${MONGOSH_VERSION}" ]]
}

@test "mongo-tools is installed and version is ${MONGO_TOOLS_VERSION}" {
    run mongodump --version
    [ "$status" -eq 0 ]
    [[ "$output" == *"${MONGO_TOOLS_VERSION}"* ]]
}