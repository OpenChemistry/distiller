#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build --build-arg WORKER=scan -t openchemistry/distiller-faust-scan:$TAG -f ../Dockerfile.worker ../