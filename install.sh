#!/bin/bash
set -e

echo ">>> Updating system packages..."
sudo apt update

echo ">>> Installing Python and pip..."
sudo apt install -y python3 python3-pip

echo ">>> Installing Python requirements..."
pip3 install -r requirements.txt

echo ">>> Installation complete."
