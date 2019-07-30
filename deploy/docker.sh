#!/usr/bin/env bash
if [[ "${PWD##*/}" = "deploy" ]]; then
    cd ..
fi
if [[ "$#" < 2 ]]; then
    echo "Must provide at least two arguments: container-name, command [build, run, test]"
    exit 1
fi
if [[ $2 = "build" ]]; then
    docker build -t $1 -f deploy/Dockerfile .
elif [[ $2 = "build-and-test" ]]; then
    ./$0 $1 build
    ./$0 $1 test
elif [[ $2 = "py" ]]; then
    docker run -it $1 python3
elif [[ $2 = "run" ]]; then
    docker run -it $1 $3
elif [[ $2 = "exec" ]]; then
    docker run -it $1 $3
elif [[ $2 = "test" ]]; then
    docker run -it $1 python3 -m pytest tests/$3
elif [[ $2 = "clean" && $1 = "all" ]]; then
    docker rm $(docker ps -a -q)
    docker rmi $(docker images -q)
else
  echo "Incorrect command argument. Choices: build, run, exec, test, clean"
fi