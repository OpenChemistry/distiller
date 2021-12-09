#!/bin/sh

docker build --build-arg WORKER=custodian -t openchemistry/distiller-faust-custodian -f ../Dockerfile.worker ../