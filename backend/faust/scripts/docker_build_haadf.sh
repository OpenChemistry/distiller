#!/bin/sh

docker build --build-arg WORKER=haadf -t openchemistry/distiller-faust-haadf -f ../Dockerfile.worker ../