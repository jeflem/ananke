#!/bin/bash

source ./config.sh

read -p "Do you really want to remove container $CONTAINER_NAME? Modifications inside the container will be lost! (y/n) " yn
case $yn in
    [yY] ) echo "Removing container...";;
    [nN] ) echo "Exiting..."; exit;;
    * ) echo "Invalid response!"; exit;;
esac

systemctl --user stop $CONTAINER_NAME.service

rm $CONTAINER_NAME.container
rm $SYSTEMD_PATH/$CONTAINER_NAME.container

systemctl --user daemon-reload
