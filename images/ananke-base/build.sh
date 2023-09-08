#!/bin/bash

IMAGE_NAME=ananke-base

podman build --tag=$IMAGE_NAME .
