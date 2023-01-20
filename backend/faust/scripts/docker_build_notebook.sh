#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build  --build-arg WORKER=notebook -t openchemistry/distiller-faust-notebook:$TAG -f ../Dockerfile.notebook_worker ../ $@