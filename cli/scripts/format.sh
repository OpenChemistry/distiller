#!/bin/sh -e
set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place distiller --exclude=__init__.py
black distiller
isort distiller
