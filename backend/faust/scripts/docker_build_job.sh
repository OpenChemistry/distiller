#!/bin/sh

docker build -t openchemistry/distiller-faust-job -f ../Dockerfile.job_worker ../ $@
