#!/bin/bash
set -e
mkdir -p ~/.docker
echo '{ "credsStore": "" }' > ~/.docker/config.json
sudo chown root:huloop /var/run/docker.sock
