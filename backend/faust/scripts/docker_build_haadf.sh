#!/bin/sh

docker build --build-arg WORKER=haadf -t openchemistry/still-faust-haadf -f ../Dockerfile.worker ../