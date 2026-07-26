#!/bin/bash
set -e

type -P python3 >/dev/null 2>&1 || {
    echo "Python 3 is required."
    exit 1
}

if [ ! -f /.dockerenv ]; then
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi

    source .venv/bin/activate

    if [ ! -f ".venv/.installed" ]; then
        pip install -r requirements.txt
        touch .venv/.installed
    fi
fi

echo "Updating yt-dlp..."
pip install -U yt-dlp

echo "Starting tt2yt..."
python3 src/main.py "$@"