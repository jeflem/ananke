#!/bin/bash

CONTAINER_NAME=ananke-nbgrader-hub

read -p "Do you really want to remove container $CONTAINER_NAME? Modifications inside the container will be lost! (y/n) " yn
case $yn in
    [yY] ) echo "Removing container...";;
    [nN] ) echo "Exiting..."; exit;;
    * ) echo "Invalid response!"; exit;;
esac

systemctl --user stop container-$CONTAINER_NAME
systemctl --user disable container-$CONTAINER_NAME

rm ~/.config/systemd/user/container-$CONTAINER_NAME.service

podman rm $CONTAINER_NAME
 
