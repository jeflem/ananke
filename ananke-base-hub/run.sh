#!/bin/bash

IMAGE_NAME=ananke-base
CONTAINER_NAME=ananke-base-hub
PORT=8000

echo "Creating container..."

podman create \
-p $PORT:8000 \
--cap-add SYS_ADMIN \
--mount=type=bind,source=runtime/dyn_home,destination=/var/lib/private \
--mount=type=bind,source=runtime/jupyterhub_config.d,destination=/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d \
-m=8g \
--name=$CONTAINER_NAME \
$IMAGE_NAME

mkdir -p ~/.config/systemd/user
podman generate systemd --restart-policy=always --name $CONTAINER_NAME > ~/.config/systemd/user/container-$CONTAINER_NAME.service
systemctl --user daemon-reload
systemctl --user enable container-$CONTAINER_NAME.service

echo "Starting container..."
systemctl --user start container-$CONTAINER_NAME.service
