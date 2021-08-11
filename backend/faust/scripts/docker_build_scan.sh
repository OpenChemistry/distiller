#!/bin/sh

docker build --build-arg WORKER=scan -t openchemistry/still-faust-scan -f ../Dockerfile.worker ../