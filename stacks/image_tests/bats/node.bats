#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(NODE_VERSION WF_NODE_VERSION)

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

@test "node is installed and version is in (\${NODE_VERSION}, \${WF_NODE_VERSION})" {
    expected_versions=()
    [ -n "$NODE_VERSION" ] && expected_versions+=("$NODE_VERSION")
    [ -n "$WF_NODE_VERSION" ] && expected_versions+=("$WF_NODE_VERSION")
    run node --version
    [ "$status" -eq 0 ]
    version_ok=false
    for v in "${expected_versions[@]}"; do
        if [[ "$output" == v${v}* ]]; then
            version_ok=true
            break
        fi
    done
    [ "$version_ok" = true ]
}

@test "npm is installed" {
    run npm --version
    [ "$status" -eq 0 ]
}
