#!/bin/sh

docker build --build-arg WORKER=base -t openchemistry/still-faust-base -f ../Dockerfile.base ../ $@