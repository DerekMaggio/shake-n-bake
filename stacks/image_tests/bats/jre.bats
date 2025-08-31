#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(JAVA_VERSION)

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

@test "jre is installed under /opt/zulu-jre and version is ${JAVA_VERSION}" {
    run /opt/zulu-jre/bin/java -version
    [ "$status" -eq 0 ]
    [[ "$output" == *"${JAVA_VERSION}"* ]]
}

@test "JRE_HOME is set to /opt/zulu-jre" {
    run echo "$JRE_HOME"
    [ "$status" -eq 0 ]
    [[ "$output" == "/opt/zulu-jre" ]]
}

@test "java is available in the PATH" {
    run which java
    [ "$status" -eq 0 ]
    [[ "$output" == "/opt/zulu-jre/bin/java" ]]
}
