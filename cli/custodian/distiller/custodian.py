#!/usr/bin/env python3

#
# "command server" used in conjection with authorized_keys command to restrict
# operations to just what is required for managing and transfering scans. Supported
# operations include listing scan data files, removing all files assocated with
# a scan and bbcp SRC.
#
# Usage:
#
# command="/path/to/this/script/distiller $SSH_ORIGINAL_COMMAND",no-port-forwarding,no-x11-forwarding,no-agent-forwarding,no-pty ...
#

import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import coloredlogs
from config import settings

DATA_FILE_GLOB_PATTERN = "data_scan{scan_id}_module*_dst*_file*.data"
LOG_FILE_GLOB_PATTERN = "log_scan{scan_id}_to*_module*_dst*_file*.data"

COMMANDS = ["rm", "ls", "bbcp"]

# Setup logger
# Setup logger
logger = logging.getLogger("custodian")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = coloredlogs.ColoredFormatter(
    "%(asctime)s,%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
if settings.LOG_FILE_PATH is not None:
    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH, maxBytes=102400, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def _traverse(args, patterns, func):
    if len(args) < 2:
        logger.error(f"Invalid number of arguments.")
        raise ValueError()

    scan_id = int(args[0])
    paths = args[1:]

    # Validate paths
    paths = [p for p in paths if p in settings.SCAN_DIRECTORIES]

    logger.info(f"Traversing file for scan {scan_id} in {paths}.")

    zero_padded_scan_id = f"{scan_id:010}"

    # Render the scan id into the glob patterns
    patterns = [pattern.format(scan_id=zero_padded_scan_id) for pattern in patterns]

    logger.info(f"Glob patterns: {patterns}")

    # Check all paths exist
    for path in paths:
        if not Path(path).exists():
            logger.error(f"Path doesn't exist: {path}")
            raise ValueError()

    # Loop through patterns and paths
    for pattern in patterns:
        for path in paths:
            for p in Path(path).glob(pattern):
                logger.info(f"Calling {func} for {p}.")
                func(p)


def _rm(args):
    patterns = [
        DATA_FILE_GLOB_PATTERN,
        LOG_FILE_GLOB_PATTERN,
    ]

    logger.info("Removing scan files.")

    _traverse(args, patterns, os.unlink)


def _ls(args):
    patterns = [
        DATA_FILE_GLOB_PATTERN,
    ]

    logger.info("Listing scan files.")

    _traverse(args, patterns, print)


def _bbcp(args):
    logger.info("bbcp command.")

    # Validate the args
    if len(args) != 2 or args[1] != "SRC":
        logger.error(f"Invalid args: {args}")
        raise ValueError()

    # Exectute the original bbcp command
    subprocess.call(args)


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        return

    command = args[0]

    if command not in COMMANDS:
        return

    try:
        if command == "rm":
            _rm(args[1:])
        elif command == "ls":
            _ls(args[1:])
        elif command == "bbcp":
            _bbcp(args)
        else:
            logger.error(f"Invalid command: {command}")

    except ValueError:
        logger.info("Invalid command")


if __name__ == "__main__":
    main()
