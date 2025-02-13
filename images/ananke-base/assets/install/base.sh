#!/bin/bash

NUMPY_VERSION=2.2.3
PANDAS_VERSION=2.2.3

MATPLOTLIB_VERSION=3.10.0
IPYMPL_VERSION=0.9.6
# ipympl is required in both jhub and python3 env for interactive matplotlib output
SEABORN_VERSION=0.13.2

PLOTLY_VERSION=6.0.0
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
pip install ipympl==$IPYMPL_VERSION
