#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install jupyter-collaboration==2.1.2

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
jupyter labextension unlock @jupyter/collaboration-extension
jupyter labextension disable @jupyter/docprovider-extension
jupyter labextension unlock @jupyter/docprovider-extension
