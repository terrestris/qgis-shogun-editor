#!/bin/bash

xhost +

function resetxhost {
  echo "Resetting xhost"
  xhost -
}

trap resetxhost EXIT
docker compose -f docker/docker-compose-dev.yml up

#--force-recreate
