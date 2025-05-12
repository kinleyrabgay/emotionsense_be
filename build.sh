#!/bin/bash

# Exit on error
set -e

echo "Installing Python dependencies..."
# Install essential packages first
pip install wheel setuptools pip --upgrade

# Install OpenCV dependencies
pip install opencv-python

# Install TensorFlow and its dependencies
pip install tensorflow tensorboard numpy ml_dtypes>=0.5.1

# Install remaining packages
pip install --no-deps -r requirements.txt

echo "Setting up environment..."
python -m app.database.migrations

echo "Setup completed successfully" 