# config file for creating an Ananke container

config['image_name'] = 'ananke-base:latest'
config['port'] = 8000

# additional arguments to Podman
config['podman_args'] = []
config['podman_args'].append('-m=8g')  # limit memory to 8 GB per user

# host directories accessible inside the container
# (paths have to be absolute or relative to config file path)
config['volumes'] = []
