#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install --root-user-action=ignore jupyter-collaboration==4.3.0
pip install --root-user-action=ignore jupyter_server_nbmodel[lab]

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
jupyter labextension unlock @jupyter/collaboration-extension
jupyter labextension disable @jupyter/docprovider-extension
jupyter labextension unlock @jupyter/docprovider-extension
jupyter labextension disable @datalayer/jupyter-server-nbmodel
jupyter labextension unlock @datalayer/jupyter-server-nbmodel
