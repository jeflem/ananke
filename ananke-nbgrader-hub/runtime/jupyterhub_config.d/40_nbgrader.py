# configure nbgrader and Kore

c = get_config()  # noqa
 
# make nbgrader log and exchange dir user writable
c.SystemdSpawner.readwrite_paths.extend(['/opt/conda/envs/jhub/share/jupyter/nbgrader.log', '/opt/nbgrader_exchange'])

# Kore config
load_subconfig('/opt/kore/kore_jhub_config.py')
