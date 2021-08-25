#!/bin/sh

docker build --build-arg WORKER=scan -t openchemistry/distiller-faust-scan -f ../Dockerfile.worker ../