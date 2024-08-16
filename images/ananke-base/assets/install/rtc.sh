#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install jupyter-collaboration==3.0.0b2

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
jupyter labextension unlock @jupyter/collaboration-extension
