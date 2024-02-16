#!/bin/bash

IMAGE_NAME=test-moodle

podman build --tag=$IMAGE_NAME .
