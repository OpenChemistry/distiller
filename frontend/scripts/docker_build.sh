#!/bin/sh

TAG=`git log -1 --pretty=%h`

docker build --build-arg REACT_APP_SENTRY_DSN_URL=$REACT_APP_SENTRY_DSN_URL -t openchemistry/distiller-client:$TAG -f ../Dockerfile ../ $@
