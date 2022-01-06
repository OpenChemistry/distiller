#!/bin/bash

# if UMASK has been provided set it.
if [[ -v UMASK ]]; then
umask $UMASK
fi

faust -A ${WORKER}_worker worker -l info