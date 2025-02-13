#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install jupyter-collaboration==3.1.0
pip install jupyter_server_nbmodel[lab]

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
jupyter labextension unlock @jupyter/collaboration-extension
jupyter labextension disable @jupyter/docprovider-extension
jupyter labextension unlock @jupyter/docprovider-extension
jupyter labextension disable jupyter-server-nbmodel
jupyter labextension unlock jupyter-server-nbmodel
