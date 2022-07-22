#!/bin/sh
TAG=`git log -1 --pretty=%h`

docker build --build-arg WORKER=custodian -t openchemistry/distiller-faust-custodian:$TAG -f ../Dockerfile.worker ../
