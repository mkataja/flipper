#!/bin/zsh

set -e

export FLIPPER_UID=$(id -u flipper)
export FLIPPER_GID=$(id -g flipper)

docker compose -f ./docker-compose-run.yaml up --build -d --no-recreate flipper

