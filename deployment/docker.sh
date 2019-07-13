#!/usr/bin/env bash
if [[ "${PWD##*/}" = "deployment" ]]; then
    cd ..
fi
if [[ "$#" -ne 2 ]]; then
    echo "Must provide two arguments: container-name, command [build, run, test]"
    exit 1
fi
if [[ $2 = "build" ]]; then
   docker build -t $1 -f deployment/Dockerfile . | grep "^Step" | while read line ; do echo "[$(date "+%H:%M:%S")] | $line"; done;
   docker run -it $1 python3 -m pytest PySeal/tests/
elif [[ $2 = "run" ]]; then
   docker run -it $1 python3
elif [[ $2 = "test" ]]; then
   docker run -it $1 python3 -m pytest PySeal/tests/
else
  echo "Incorrect command argument. Choices: build, run, test"
fi