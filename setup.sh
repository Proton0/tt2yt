#!/bin/bash

INSTALL_REQUIREMENTS=false

type -P python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is required. Please install it!"; exit 1; }

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found, creating one"
  python3 -m venv .venv
  INSTALL_REQUIREMENTS=true
fi

source .venv/bin/activate

if [ "$INSTALL_REQUIREMENTS" = true ]; then
  echo "Installing requirements"
  pip install -r requirements.txt
fi

if [ ! -d "secrets" ]; then
    echo "Warning: Secrets directory not found! Refer to the README for instructions"
    exit 1
fi

echo "Setup complete. You can run tt2yt now"