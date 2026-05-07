#!/bin/bash

timedatectl set-timezone $TZ

test -e /opt/ca.pem && cp /opt/ca.pem /usr/local/share/ca-certificates/ca.crt && update-ca-certificates

# make JupyterHub cookie secret
touch /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
openssl rand -hex 32 > /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
chmod 600 /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret
