#!/usr/bin/env bash
if [[ "${PWD##*/}" = "deployment" ]]; then
    cd ..
fi
if [[ "$#" -ne 1 ]]; then
    echo "Must provide two arguments: container-name, command [build, run]"
fi
if [[ $2 = "build" ]]; then
   docker build -t $1 -f deployment/Dockerfile .
elif [[ $2 = "run" ]]; then
   docker run -it $1 python3
else
  echo "Incorrect command argument. Choices: build, run"
fi