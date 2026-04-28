#!/bin/bash

IMAGE_NAME=localhost/test-moodle
CONTAINER_NAME=test-moodle
PORT=9001
TIME_ZONE=Europe/Berlin

SYSTEMD_PATH=~/.config/containers/systemd
UNIT_FILE=$SYSTEMD_PATH/$CONTAINER_NAME.container
RUNTIME_DIR=$(pwd)/runtime
