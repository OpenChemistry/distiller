#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build -t openchemistry/distiller-scan-service:$TAG -f ../Dockerfile ../ $@
