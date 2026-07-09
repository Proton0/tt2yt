#!/bin/bash

type -P python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is required. Please install it!"; exit 1; }

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found, please run setup.sh or install the requirements manually"
  exit 1
fi

source .venv/bin/activate

python3 src/main.py