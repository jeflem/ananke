#!/bin/bash

source /opt/conda/etc/profile.d/conda.sh

conda activate python3

read -p "Install GPU support for TensorFlow? (y/n) " yn
case $yn in
    [yY] ) TF_VARIANT="tensorflow[and-cuda]";;
    [nN] ) TF_VARIANT="tensorflow-cpu";;
    * ) echo "Invalid response!"; TF_VARIANT="invalid";;
esac

if [ "$TF_VARIANT" != "invalid" ]; then

    # downgrade Python
    conda install -y python==3.12.7

    # install TensorFlow
    pip install --root-user-action=ignore $TF_VARIANT==2.21.0
    pip install --root-user-action=ignore keras_tuner

    # test
    echo "----------------------------------------------"
    echo "listing GPUs available to TensorFlow..."
    python3 -c "import tensorflow as tf; print('GPU devices:', tf.config.list_physical_devices('GPU'))"
    echo "----------------------------------------------"
    echo "testing TensorFlow..."
    python3 -c "import tensorflow as tf; print('computation test:', tf.reduce_sum(tf.random.normal([1000, 1000])))"
    echo "----------------------------------------------"
    echo "done"

fi
