# config file for creating an Ananke container

config['image_name'] = 'ananke-base:latest'
config['port'] = 8000

# memory limit for container ('interactive', '8g', '500m',...)
config['memory'] = 'interactive'

# maximum number of CPUs (cores) available to the container ('interactive', 1, 2,..., 'max')
config['cpus'] = 'interactive'

# additional arguments to Podman
config['podman_args'] = []

# host directories accessible inside the container
# (paths have to be absolute or relative to config file path)
config['volumes'] = []
