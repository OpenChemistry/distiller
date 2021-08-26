#!/bin/sh

docker build --build-arg WORKER=cron -t openchemistry/distiller-faust-cron -f ../Dockerfile.worker ../ $@
