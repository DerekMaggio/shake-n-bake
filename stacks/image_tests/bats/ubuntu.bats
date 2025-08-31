#! /usr/bin/env bats

load '/opt/bats/plugins/bats-file/load'

@test "user 'ubuntu' does not exist" {
  ! id -u ubuntu &>/dev/null
}

@test "$USER_NAME user exists" {
  run id -u "$USER_NAME"
  [ "$status" -eq 0 ]
}

@test "$USER_NAME user has a home directory" {
  run test -d "$USER_HOME"
  run test -d "/home/$USER_NAME"
  [ "$status" -eq 0 ]
}

@test "$GROUP_NAME group exists" {
  run getent group "$GROUP_NAME"
  [ "$status" -eq 0 ]
}

@test "yq is installed and version is ${YQ_VERSION}" {
  run yq --version
  [ "$status" -eq 0 ]
  [[ "$output" == *"v${YQ_VERSION}"* ]]
}