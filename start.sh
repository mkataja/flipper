#!/bin/zsh

set -e

export FLIPPER_UID=$(id -u flipper)
export FLIPPER_GID=$(id -g flipper)

if [ $1 = "build" ]; then
  docker compose build
fi
docker compose up --build -d --no-recreate flipper

