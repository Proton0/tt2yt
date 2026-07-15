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

TIKTOK_USERNAME=""
OPENROUTER_API_KEY=""
CLIENT_SECRETS=""

while getopts "t:o:c:" opt; do
  case $opt in
    t)
      TIKTOK_USERNAME="$OPTARG"
      ;;
    o)
      OPENROUTER_API_KEY="$OPTARG"
      ;;
    c)
      CLIENT_SECRETS="$OPTARG"
      ;;
    *)
      echo "Usage: $0 -t <TIKTOK_USERNAME> -o <OPENROUTER_API_KEY> -c <CLIENT_SECRETS_PATH>"
      exit 1
      ;;
  esac
done

if [ ! -d "secrets" ]; then
    if [ -z "$TIKTOK_USERNAME" ] || [ -z "$OPENROUTER_API_KEY" ] || [ -z "$CLIENT_SECRETS" ]; then
        echo "Secrets not found, set them up using command line arguments (run the command below)"
        echo
        echo "Usage: $0 -t <TIKTOK_USERNAME> -o <OPENROUTER_API_KEY> -c <CLIENT_SECRETS_PATH>"
        exit 1
    fi
else
    if [ -z "$CLIENT_SECRETS" ]; then
        CLIENT_SECRETS="secrets/client_secrets.json"
    fi
fi

echo "Environment setup complete, Running tt2yt"

# Build command
CMD=(python3 src/main.py)

[ -n "$TIKTOK_USERNAME" ] && CMD+=(-t "$TIKTOK_USERNAME")
[ -n "$OPENROUTER_API_KEY" ] && CMD+=(-o "$OPENROUTER_API_KEY")
[ -n "$CLIENT_SECRETS" ] && CMD+=(-c "$CLIENT_SECRETS")

"${CMD[@]}"
