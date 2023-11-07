#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install jupyter-collaboration==2.0.0a4

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
