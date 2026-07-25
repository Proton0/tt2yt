"""
tt2yt: TikTok to YouTube Uploader

Copyright (C) 2026 Proton0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

"""

import argparse
import json
import sys
from pathlib import Path

from tt2yt import TT2YT

SECRETS_DIR = Path("secrets")
GLOBAL_SECRETS_FILE = SECRETS_DIR / "secrets.json"


def load_global_secrets() -> dict:
    if not GLOBAL_SECRETS_FILE.is_file():
        return {}

    try:
        with GLOBAL_SECRETS_FILE.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Failed to decode {GLOBAL_SECRETS_FILE}. Using empty secrets.", file=sys.stderr)
        return {}


def save_global_secrets(secrets: dict):
    print("Saving secrets...")
    try:
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        with GLOBAL_SECRETS_FILE.open('w') as f:
            json.dump(secrets, f, indent=4)
    except Exception as e:
        print(f"Error saving secrets to {GLOBAL_SECRETS_FILE}: {e}", file=sys.stderr)


def parse_secrets(args: argparse.Namespace) -> dict:
    global_secrets = load_global_secrets()
    secrets = {}
    missing_keys = []

    tiktok_profile = args.tiktok_profile or global_secrets.get('tiktok_profile')
    if tiktok_profile:
        secrets['tiktok_profile'] = tiktok_profile

    tiktok_channel_id = args.tiktok_channel_id or global_secrets.get('tiktok_channel_id')
    if tiktok_channel_id:
        secrets['tiktok_channel_id'] = tiktok_channel_id
        print("Using TikTok channel ID")
    else:
        if not tiktok_profile:
            # Both of them are missing
            missing_keys.append("tiktok_channel_id")
            missing_keys.append("tiktok_profile")
            print("Note: More recommended to use channel ID instead of profile, but profile is also accepted.")
        else:
            print("Warning: Using tiktok profile instead of channel ID is more prone to errors.")

    openrouter_key = args.openrouter_key or global_secrets.get('openrouter_key')
    if openrouter_key:
        secrets['openrouter_key'] = openrouter_key
    else:
        secrets['openrouter_key'] = None

    client_secrets_path = args.client_secrets_file

    if client_secrets_path and Path(client_secrets_path).is_file():
        try:
            with open(client_secrets_path, 'r') as f:
                secrets['client_secrets'] = json.load(f)
        except Exception as e:
            print(f"Error loading client secrets from {client_secrets_path}: {e}", file=sys.stderr)
            missing_keys.append("client_secrets")
    elif 'client_secrets' in global_secrets:
        secrets['client_secrets'] = global_secrets['client_secrets']
    else:
        missing_keys.append("client_secrets_file")

    if not secrets.get("tiktok_channel_id") and secrets.get("tiktok_profile"):
        print("Warning: Channel ID is a lot better than using TikTok Profile.")

    if missing_keys:
        raise RuntimeError(f"Missing required configuration for: {', '.join(missing_keys)}")

    has_changes = (
        not global_secrets or
        global_secrets.get('tiktok_profile') != secrets.get('tiktok_profile') or
        global_secrets.get('openrouter_key') != secrets.get('openrouter_key') or
        'client_secrets' in secrets and global_secrets.get('client_secrets') != secrets.get('client_secrets') or
        global_secrets.get("tiktok_channel_id") != secrets.get("tiktok_channel_id")
    )

    if has_changes:
        secrets_to_save = {k: v for k, v in secrets.items() if v is not None}
        save_global_secrets(secrets_to_save)

    return secrets


def main():
    parser = argparse.ArgumentParser(description='tt2yt: TikTok to YouTube Uploader')

    parser.add_argument('-t', '--tiktok_profile', type=str, help='TikTok profile')
    parser.add_argument("-tc", "--tiktok-channel-id", type=str, help="TikTok Channel ID")
    parser.add_argument('-o', '--openrouter_key', type=str, help='OpenRouter API key')
    parser.add_argument('-c', '--client_secrets_file', type=str, help='Google client secrets file path',
                        default="secrets/client_secrets.json")

    args = parser.parse_args()

    try:
        secrets = parse_secrets(args)
        x = TT2YT(secrets, args.client_secrets_file)
        x.run()

    except RuntimeError as e:
        print(f"Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
else:
    raise ImportError("tt2yt's main.py is meant to be run as a script, not imported.")
