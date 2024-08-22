#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate python3

# downgrade Python
conda install -y python=3.10

# install
pip install numpy==1.26.4
pip install tensorflow[and-cuda]==2.17.0
pip install keras_tuner

# test
echo "----------------------------------------------"
echo "listing GPUs available to TensorFlow..."
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
echo "----------------------------------------------"
echo "testing TensorFlow..."
python3 -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"
echo "----------------------------------------------"
echo "done"
