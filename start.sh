#!/bin/zsh

set -e

export IMAGE_TAG=$(date +"%Y%m%dT%H%M%S")

export FLIPPER_UID=$(id -u flipper)
export FLIPPER_GID=$(id -g flipper)

nocache=false
for arg in "$@"; do
  if [[ "$arg" == "--no-cache" ]]; then
    nocache=true
    break
  fi
done

if $nocache; then
  echo "Not using build cache"
  docker compose build --no-cache
else
  echo "NOTE: Using build cache"
  sleep 1
  docker compose build
fi

docker tag flipper:$IMAGE_TAG flipper:latest

docker compose up --build -d flipper
