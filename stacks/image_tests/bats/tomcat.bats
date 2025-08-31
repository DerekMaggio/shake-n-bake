#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

REQUIRED_ENV_VARS=(TOMCAT_VERSION USER_HOME)

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

@test "tomcat is installed in ${USER_HOME}/tomcat" {
    assert_dir_exists "${USER_HOME}/tomcat"
    assert_file_exists "${USER_HOME}/tomcat/bin/catalina.sh"
}

@test "tomcat version is ${TOMCAT_VERSION}" {
    run ${USER_HOME}/tomcat/bin/version.sh
    [ "$status" -eq 0 ]
    [[ "$output" == *"${TOMCAT_VERSION}"* ]]
}

@test "catalina script is executable" {
    run test -x "${USER_HOME}/tomcat/bin/catalina.sh"
    [ "$status" -eq 0 ]
}
