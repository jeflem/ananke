c = get_config()

# -----------------------------------------------------------------------------
# configuration for nb_conda_kernels

# install kernels locally for each user
c.CondaKernelSpecManager.kernelspec_path='--user'

# use kernels' original display_name property for display in JupyterLab
c.CondaKernelSpecManager.name_format='{display_name}'

# ignore kernels of global envs (they are available by default)
c.CondaKernelSpecManager.env_filter = '/opt/conda/envs'
