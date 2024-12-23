#!/bin/zsh

set -e

export FLIPPER_UID=$(id -u flipper)
export FLIPPER_GID=$(id -g flipper)

if [[ $1 == "build" ]]; then
  echo "Rebuild requested"
  docker compose build --no-cache
fi
docker compose up --build --no-recreate -d flipper

