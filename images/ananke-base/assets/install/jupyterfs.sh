#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub

# SMB support for jupyterfs via fsspec
conda install -y fsspec smbprotocol

# WebDAV support for jupyterfs via pyfs
pip install --root-user-action=ignore fs.webdavfs

pip install --root-user-action=ignore jupyter-fs==1.1.2

# jupyter-fs doesn't work with newer versions of setuptools (downgrade!)
conda install -y setuptools==81.0.0

# config file
cp /opt/install/jupyter_server_config_jupyterfs.py /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_jupyterfs.py
touch /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
chmod 644 /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
echo "load_subconfig('/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_jupyterfs.py')" >> /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
