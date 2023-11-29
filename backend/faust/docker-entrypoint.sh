#!/bin/bash

# if UMASK has been provided set it.
if [[ -v UMASK ]]; then
umask $UMASK
fi

python -m faust -A ${WORKER}_worker worker -l info --without-web