#!/bin/sh

docker build --build-arg WORKER=base -t openchemistry/distiller-faust-base -f ../Dockerfile.base ../ $@