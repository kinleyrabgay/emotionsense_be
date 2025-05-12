#!/bin/bash

# Exit on error
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Setting up environment..."
python -m app.database.migrations

echo "Setup completed successfully" 