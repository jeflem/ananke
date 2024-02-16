#!/bin/bash

IMAGE_NAME=test-moodle
CONTAINER_NAME=test-moodle
PORT=9090

echo "Creating container..."

podman create \
-p $PORT:80 \
--cap-add SYS_ADMIN \
--mount=type=bind,source=runtime/mariadb_data,destination=/var/lib/mysql \
--mount=type=bind,source=runtime/moodle_data,destination=/opt/moodledata \
-m=4g \
--name=$CONTAINER_NAME \
$IMAGE_NAME

mkdir -p ~/.config/systemd/user
podman generate systemd --restart-policy=always --name $CONTAINER_NAME > ~/.config/systemd/user/container-$CONTAINER_NAME.service
systemctl --user daemon-reload
systemctl --user enable container-$CONTAINER_NAME.service

echo "Starting container..."
systemctl --user start container-$CONTAINER_NAME.service
