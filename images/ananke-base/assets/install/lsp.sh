#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
conda install -y jupyterlab-lsp jupyter-lsp-python

# config file
cp /opt/install/jupyter_server_config_lsp.py /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_lsp.py
touch /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
chmod 644 /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
echo "load_subconfig('/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_lsp.py')" >> /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
