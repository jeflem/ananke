#!/bin/bash

timedatectl set-timezone Europe/Berlin

# make JupyterHub cookie secret
touch /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
openssl rand -hex 32 > /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
chmod 600 /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret
