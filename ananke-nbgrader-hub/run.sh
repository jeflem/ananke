#!/bin/bash

IMAGE_NAME=ananke-nbgrader
CONTAINER_NAME=ananke-nbgrader-hub
PORT=8000

echo "Creating container..."

podman create \
-p $PORT:8000 \
--cap-add SYS_ADMIN \
--mount=type=bind,source=runtime/dyn_home,destination=/var/lib/private \
--mount=type=bind,source=runtime/jupyterhub_config.d,destination=/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d \
--mount=type=bind,source=runtime/home,destination=/home \
--mount=type=bind,source=runtime/kore,destination=/opt/kore/runtime \
--mount=type=bind,source=runtime/nbgrader_exchange,destination=/opt/nbgrader_exchange \
-m=8g \
--name=$CONTAINER_NAME \
$IMAGE_NAME

mkdir -p ~/.config/systemd/user
podman generate systemd --restart-policy=always --name $CONTAINER_NAME > ~/.config/systemd/user/container-$CONTAINER_NAME.service
systemctl --user daemon-reload
systemctl --user enable container-$CONTAINER_NAME.service

echo "Starting container..."
systemctl --user start container-$CONTAINER_NAME.service
