#!/bin/bash

function refresh_aliases() {
    cp /workspaces/huloop-dev-tools/dockerfiles/util/huloop-dev-tools/.bash_aliases ${HOME}/.bash_aliases
    source ${HOME}/.bash_aliases
}


alias dive="docker run -ti --rm  -v /var/run/docker.sock:/var/run/docker.sock docker.io/wagoodman/dive"