#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build --build-arg WORKER=cron -t openchemistry/distiller-faust-cron:$TAG -f ../Dockerfile.worker ../ $@
