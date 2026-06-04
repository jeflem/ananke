#!/bin/bash

source ./config.sh

mkdir -p $RUNTIME_DIR
test ! -e $RUNTIME_DIR/mariadb_data && \
    IMG_DIR=$(podman unshare podman image mount "$IMAGE_NAME") && \
    podman unshare cp -r "$IMG_DIR/var/lib/mysql" "$RUNTIME_DIR/mariadb_data" && \
    podman unshare podman image umount "$IMAGE_NAME" > /dev/null && \
    chmod -R a+rwX "$RUNTIME_DIR/mariadb_data"
test ! -e $RUNTIME_DIR/moodle_data && \
    IMG_DIR=$(podman unshare podman image mount "$IMAGE_NAME") && \
    podman unshare cp -r "$IMG_DIR/opt/moodledata" "$RUNTIME_DIR/moodle_data" && \
    podman unshare podman image umount "$IMAGE_NAME" > /dev/null && \
    chmod -R a+rwX "$RUNTIME_DIR/moodle_data"
test ! -e $RUNTIME_DIR/moodle_code && \
    IMG_DIR=$(podman unshare podman image mount "$IMAGE_NAME") && \
    podman unshare cp -r "$IMG_DIR/var/www/html/moodle" "$RUNTIME_DIR/moodle_code" && \
    podman unshare podman image umount "$IMAGE_NAME" > /dev/null

mkdir -p $SYSTEMD_PATH
touch $UNIT_FILE
echo "[Unit]" >> $UNIT_FILE
echo "Description=$CONTAINER_NAME container" >> $UNIT_FILE
echo "" >> $UNIT_FILE
echo "[Container]" >> $UNIT_FILE
echo "Image=$IMAGE_NAME" >> $UNIT_FILE
echo "ContainerName=$CONTAINER_NAME" >> $UNIT_FILE
echo "PublishPort=$PORT:80" >> $UNIT_FILE
echo "EnvironmentFile=\"$(pwd)/container.env\"" >> $UNIT_FILE
echo "Mount=type=bind,source=$RUNTIME_DIR/mariadb_data,destination=/var/lib/mysql" >> $UNIT_FILE
echo "Mount=type=bind,source=$RUNTIME_DIR/moodle_data,destination=/opt/moodledata" >> $UNIT_FILE
echo "Mount=type=bind,source=$RUNTIME_DIR/moodle_code,destination=/var/www/html/moodle" >> $UNIT_FILE
echo "Mount=type=bind,source=$(pwd)/container.env,destination=/opt/container.env" >> $UNIT_FILE
test -e $(pwd)/ca.pem && echo "Mount=type=bind,source=$(pwd)/ca.pem,destination=/opt/ca.pem" >> $UNIT_FILE
echo "AddCapability=SYS_ADMIN" >> $UNIT_FILE
echo "" >> $UNIT_FILE
echo "[Install]" >> $UNIT_FILE
echo "WantedBy=default.target" >> $UNIT_FILE

ln -s $UNIT_FILE $CONTAINER_NAME.container

#/usr/lib/systemd/user-generators/podman-user-generator --dryrun

systemctl --user daemon-reload
systemctl --user start $CONTAINER_NAME.service
