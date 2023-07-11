#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build -t openchemistry/distiller-client:$TAG -f ../Dockerfile ../ $@
