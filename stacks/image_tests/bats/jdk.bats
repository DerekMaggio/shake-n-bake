#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(JAVA_VERSION MAVEN_VERSION)

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

@test "jdk is installed under /opt/zulu-jdk and version is ${JAVA_VERSION}" {
    run /opt/zulu-jdk/bin/java -version
    [ "$status" -eq 0 ]
    [[ "$output" == *"${JAVA_VERSION}"* ]]
}

@test "JAVA_HOME is set to /opt/zulu-jdk" {
    run echo "$JAVA_HOME"
    [ "$status" -eq 0 ]
    [[ "$output" == "/opt/zulu-jdk" ]]
}

@test "java is available in the PATH" {
    run which java
    [ "$status" -eq 0 ]
    [[ "$output" == "/opt/zulu-jdk/bin/java" ]]
}

@test "Maven is installed and version is ${MAVEN_VERSION}" {
    run mvn -version
    [ "$status" -eq 0 ]
    [[ "$output" == *"${MAVEN_VERSION}"* ]]
}