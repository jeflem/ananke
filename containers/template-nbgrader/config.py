# config file for creating an Ananke container

config['image_name'] = 'ananke-base:latest'
config['port'] = 8000

# memory limit for container ('interactive', '8g', '500m',...)
config['memory'] = 'interactive'

# additional arguments to Podman
config['podman_args'] = []

# host directories accessible inside the container
# (paths have to be absolute or relative to config file path)
config['volumes'] = []
config['volumes'].append(('kore', '/opt/kore/runtime'))
config['volumes'].append(('nbgrader_exchange', '/opt/nbgrader_exchange'))
