#!/bin/sh

docker build --build-arg WORKER=cron -t openchemistry/still-faust-cron -f ../Dockerfile.worker ../ $@
