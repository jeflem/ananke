#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub

# development version of webdav-client
# has bug fix for
# sed -i 's/root=self.webdav.root, path=urn.path()/root=unquote(self.webdav.root), path=urn.path()/' \
#     /opt/conda/envs/jhub/lib/python3.11/site-packages/webdav3/client.py
pip install git+https://github.com/ezhov-evgeny/webdav-client-python-3.git@98c23d1abd15efc3db9cfc756429f00041578bc2

# install jupyter-fs from fork that does not use async defs
# cf. https://github.com/jpmorganchase/jupyter-fs/issues/181
pip install git+https://github.com/jeflem/jupyter-fs.git@ananke_0.3

# WebDAV support for jupyterfs
pip install fs.webdavfs

# config file
cp /opt/install/jupyter_server_config_jupyterfs.py /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_jupyterfs.py
touch /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
chmod 644 /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
echo "load_subconfig('/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_jupyterfs.py')" >> /opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py
