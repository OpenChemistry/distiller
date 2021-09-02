#!/bin/sh

docker build -t openchemistry/distiller-faust-base -f ../Dockerfile.base ../ $@