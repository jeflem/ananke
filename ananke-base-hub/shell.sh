#!/bin/bash

source config.sh

podman exec -it "$CONTAINER_NAME" /bin/bash
