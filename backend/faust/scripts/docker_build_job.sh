#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build -t openchemistry/distiller-faust-job:$TAG -f ../Dockerfile.job_worker ../ $@
