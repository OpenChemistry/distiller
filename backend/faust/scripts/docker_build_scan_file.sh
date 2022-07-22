#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build --build-arg WORKER=scan_file -t openchemistry/distiller-faust-scan-file:$TAG -f ../Dockerfile.worker ../