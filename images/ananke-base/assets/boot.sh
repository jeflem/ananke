#!/bin/bash

timedatectl set-timezone $TZ

# install CA cert to system cert store
test -e /opt/ca.pem && cp /opt/ca.pem /usr/local/share/ca-certificates/ca.crt && update-ca-certificates

# install CA cert to certifi's cert store
# (FIX ME: avoid re-execution on second boot)
source /opt/conda/etc/profile.d/conda.sh
conda activate jhub
test -e /opt/ca.pem && cat /opt/ca.pem >> $(python -c "import certifi; print(certifi.where())")

# make JupyterHub cookie secret
# (FIX ME: avoid re-execution on second boot)
touch /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
openssl rand -hex 32 > /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret && \
chmod 600 /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret
