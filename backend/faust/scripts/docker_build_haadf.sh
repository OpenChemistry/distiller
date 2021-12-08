#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build --build-arg WORKER=haadf -t openchemistry/distiller-faust-haadf:$TAG -f ../Dockerfile.worker ../