#!/bin/bash

IMAGE_NAME=ananke-nbgrader

podman build --tag=$IMAGE_NAME .
