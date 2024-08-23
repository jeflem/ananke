#!/bin/bash

# Constants and Configuration
# ---------------------------

source config.sh

IMAGE_NAME=ananke-nbgrader
DEFAULT_PORT=8000

SCRIPT_DIRECTORY="$(dirname "$(realpath "$0")")"

CONFIG_FILE_ROOT="$SCRIPT_DIRECTORY/runtime/jupyterhub_config.d"
USER_CONFIG_FILE="$CONFIG_FILE_ROOT/20_users.py"
LMS_CONFIG_FILE="$CONFIG_FILE_ROOT/30_lms.py"

DYN_HOME_DIRECTORY="$SCRIPT_DIRECTORY/runtime/dyn_home"
HOME_DIRECTORY="$SCRIPT_DIRECTORY/runtime/home"
NBGRADER_EXCHANGE_DIRECTORY="$SCRIPT_DIRECTORY/runtime/nbgrader_exchange"
KORE_DIRECTORY="$SCRIPT_DIRECTORY/runtime/kore"


# Functions
# ---------

# Function to check if given directory exists, otherwise it will be created.
check_and_create_directory() {
  if [ ! -d "$1" ]; then
    mkdir -p "$1"
  fi
}

# Function to validate input as a 4 or 5 digit number greater than 1024, used for validating the port input by the user.
validate_input() {
  local custom_port="$1"

  [[ -n "$custom_port" && "$custom_port" =~ ^[1-9][0-9]{3,4}$ && "$custom_port" -gt 1024 && "$custom_port" -lt 49151 ]]
}

# Function to extract and process available GPUs from the YAML file.
extract_gpus() {
  local yaml_file="$1"

  if [ -f "$yaml_file" ]; then
    mapfile -t name_values < <(grep -oP '(?<=\sname:\s)\S+' "$yaml_file" | sed 's/^"\(.*\)"$/\1/' | grep -v '^all$')
  else
    name_values=()
  fi
}

# Function to display the menu
display_menu() {
  echo "Select or deselect the GPUs (type the number and press Enter):"
  for i in "${!name_values[@]}"; do
    status="[ ]"
    if [[ " ${selected[*]} " =~ " ${name_values[$i]} " ]]; then
      status="[x]"
    fi
    echo "$((i+1))) $status - GPU ${name_values[$i]}"
  done
  echo "x) Select all GPUs"
  echo ""
  echo "a) Accept"
  echo "c) Cancel"
}


# Main Script Logic
# -----------------

# Check if 20_users.py and 30_lms.py files are present. Otherwise the user gets a prompt to create them and re-execute the script.
if [ ! -e "$USER_CONFIG_FILE" ] && [ ! -e "$LMS_CONFIG_FILE" ]; then
  echo "Configuration file for users ($USER_CONFIG_FILE) and the learn management system ($LMS_CONFIG_FILE) do not exist. Please supply these files and run the script again again afterwards. You may find templates of how these files should look like in the jupyterhub_config.d directory ($CONFIG_FILE_ROOT)."
  exit 1
elif [ ! -e "$USER_CONFIG_FILE" ]; then
  echo "Configuration file for users ($USER_CONFIG_FILE) does not exist. Please supply this file and run the script again again afterwards. You may find a template of how this file should look like in the jupyterhub_config.d directory ($CONFIG_FILE_ROOT)."
  exit 1
elif [ ! -e "$LMS_CONFIG_FILE" ]; then
  echo "Configuration file for users ($LMS_CONFIG_FILE) does not exist. Please supply this file and run the script again again afterwards. You may find a template of how this file should look like in the jupyterhub_config.d directory ($CONFIG_FILE_ROOT)."
  exit 1
fi

# Check if directories under /runtime/ for the user and grader user home directory as well as the nbgrader exchange directory exist.
check_and_create_directory "$DYN_HOME_DIRECTORY"
check_and_create_directory "$HOME_DIRECTORY"
check_and_create_directory "$NBGRADER_EXCHANGE_DIRECTORY"

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

# Generate list of available devices (GPUs).
extract_gpus "$GPU_YAML_FILE"

# Interactive selection loop for devices (GPUs).
if [ ${#name_values[@]} -gt 0 ]; then
  # Interactive selection loop
  while true; do
    display_menu
    read -r -p "Enter your choice: " choice

    if [[ "$choice" == "a" ]]; then
      break
    elif [[ "$choice" == "c" ]]; then
      echo "Selection canceled."
      exit 1
    elif [[ "$choice" == "x" ]]; then
      # Select all names
      selected=("${name_values[@]}")
    elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#name_values[@]} )); then
      index=$((choice-1))
      name="${name_values[$index]}"
      if [[ " ${selected[*]} " =~ " $name " ]]; then
        # Remove the name from the selected array
        selected=("${selected[@]/$name}")
      else
        # Add the name to the selected array
        selected+=("$name")
      fi
    else
      echo "Invalid choice, please try again."
    fi
  done
fi

# Creating container with given parameters.
podman_command="podman create \
  -p $PORT:8000 \
  --cap-add SYS_ADMIN \
  --mount=type=bind,source=$DYN_HOME_DIRECTORY,destination=/var/lib/private \
  --mount=type=bind,source=$CONFIG_FILE_ROOT,destination=/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d \
  --mount=type=bind,source=$HOME_DIRECTORY,destination=/home \
  --mount=type=bind,source=$KORE_DIRECTORY,destination=/opt/kore/runtime \
  --mount=type=bind,source=$NBGRADER_EXCHANGE_DIRECTORY,destination=/opt/nbgrader_exchange \
  -m=8g \
  --name=$CONTAINER_NAME"

# Generate the command from the selected names and append to podman command if it is not empty.
gpu_command=""
for name in "${selected[@]}"; do
  gpu_command+="--device nvidia.com/gpu=$name "
done

if [ -n "$gpu_command" ]; then
  podman_command+=" $gpu_command"
fi

# Execute the final podman create command.
podman_command+=" $IMAGE_NAME"
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
