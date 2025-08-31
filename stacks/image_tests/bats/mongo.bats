#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(MONGO_VERSION USER_HOME)

setup_file() {
    local MISSING_ENV_VARS=()
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_ENV_VARS+=("$var")
        fi
    done

    if [ ${#MISSING_ENV_VARS[@]} -ne 0 ]; then
        echo "The following environment variables are not set: ${MISSING_ENV_VARS[*]}"
        exit 1
    fi
}

@test "mongodb is installed and version is ${MONGO_VERSION}" {
    run ${USER_HOME}/mongodb/bin/mongod --version
    [ "$status" -eq 0 ]
    [[ "$output" == *"${MONGO_VERSION}"* ]]
}

@test "mongodb directories exist" {
    assert_dir_exists "${USER_HOME}/mongodb"
    assert_dir_exists "${USER_HOME}/mongodb/data/db"
    assert_dir_exists "${USER_HOME}/mongodb/logs"
}

@test "mongodb config exists" {
    assert_file_exists "${USER_HOME}/mongodb/mongod.conf"
}
