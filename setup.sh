#!/bin/bash

# Check if Python exists
if ! command -v python3 &>/dev/null; then
    echo "Python is not installed. Please install Python 3.x and try again."
    exit 1
fi

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
