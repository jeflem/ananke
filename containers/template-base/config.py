# config file for creating an Ananke container

# Ananke image to use ("./ananke list" shows available ones)
config['image_name'] = 'ananke-base:latest'

# port the container is accessible through (ask your host admin for this value)
config['port'] = 8000

# memory limit for container ('interactive', '500m', '8g',..., 'max')
config['memory'] = 'interactive'

# maximum number of CPUs (cores) available to the container ('interactive', 1, 2,..., 'max')
config['cpus'] = 'interactive'

# GPUs available to the container ('interactive', GPU name (string), list of GPU names (strings))
config['gpus'] = 'interactive'

# additional arguments to Podman (list of strings)
config['podman_args'] = [
    '--pids-limit -1'  # no PID limit (Podman default is 2048, which is too small)
]

# host directories accessible inside the container (list of (host_path, container_path) tuples)
# Paths have to be absolute or relative to config file path.
# Don't use ~ in paths!
config['volumes'] = []
