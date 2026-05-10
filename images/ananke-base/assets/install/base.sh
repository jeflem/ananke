#!/bin/bash

NUMPY_VERSION=2.4.3
PANDAS_VERSION=3.0.2

MATPLOTLIB_VERSION=3.10.9
IPYMPL_VERSION=0.10.0
# ipympl is required in both jhub and python3 env for interactive matplotlib output
SEABORN_VERSION=0.13.2

PLOTLY_VERSION=6.6.0
# plotly is required in both jhub and python3 env for proper rendering in JLab

source /opt/conda/etc/profile.d/conda.sh

conda activate python3
conda install -y \
      numpy=$NUMPY_VERSION \
      matplotlib=$MATPLOTLIB_VERSION \
      pandas=$PANDAS_VERSION \
      ipympl=$IPYMPL_VERSION \
      seaborn=$SEABORN_VERSION \
      plotly=$PLOTLY_VERSION \
      nbformat \
      python-kaleido
# nbformat and python-kaleido are required by plotly

conda activate jhub
conda install -y \
      plotly=$PLOTLY_VERSION

# installing ipympl with conda seems to be broken, see https://github.com/matplotlib/ipympl/issues/564
pip install --root-user-action=ignore ipympl==$IPYMPL_VERSION
