#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate jhub
pip install jupyter-collaboration==2.0.2

# disabel RTC for all users
jupyter labextension disable @jupyter/collaboration-extension
