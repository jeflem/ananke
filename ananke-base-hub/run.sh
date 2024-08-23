#!/bin/bash

# Constants and Configuration
# ---------------------------

source config.sh

IMAGE_NAME=ananke-base
DEFAULT_PORT=8000

SCRIPT_DIRECTORY="$(dirname "$(realpath "$0")")"

CONFIG_FILE_ROOT="$SCRIPT_DIRECTORY/runtime/jupyterhub_config.d"
DYN_HOME_DIRECTORY="$SCRIPT_DIRECTORY/runtime/dyn_home"


# Functions
# ---------

# Function to validate input as a 4 or 5 digit number greater than 1024, used for validating the port input by the user.
validate_input() {
  local custom_port="$1"

  [[ -n "$custom_port" && "$custom_port" =~ ^[1-9][0-9]{3,4}$ && "$custom_port" -gt 1024 && "$custom_port" -lt 49151 ]]
}


# Main Script Logic
# -----------------

# Prompt the user for a custom port.
while true; do
  read -r -e -i "$DEFAULT_PORT" -p "Enter your port (1024 ... 49151): " custom_port

  # Check if the input is valid and exit the loop, otherwise continue loop.
  if validate_input "$custom_port"; then
    PORT="$custom_port"
    break
  else
    echo "Invalid input. Please enter a valid port."
  fi
done

echo "Creating container: container image $IMAGE_NAME, container name $CONTAINER_NAME, port $PORT."

# Execute the podman create command.
podman_command="podman create \
  -p $PORT:8000 \
  --cap-add SYS_ADMIN \
  --mount=type=bind,source=$DYN_HOME_DIRECTORY,destination=/var/lib/private \
  --mount=type=bind,source=$CONFIG_FILE_ROOT,destination=/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d \
  -m=8g \
  --name=$CONTAINER_NAME \
  $IMAGE_NAME"
eval "$podman_command"

mkdir -p ~/.config/systemd/user
podman generate systemd --restart-policy=always --name "$CONTAINER_NAME" > ~/.config/systemd/user/container-"$CONTAINER_NAME".service
systemctl --user daemon-reload
systemctl --user enable container-"$CONTAINER_NAME".service

echo "Starting container..."
systemctl --user start container-"$CONTAINER_NAME".service


# Cleanup and Exit
# ----------------

echo "Container created and started successfully!"