# tt2yt: TikTok to YouTube Shorts Uploader

[![OpenRouter](https://img.shields.io/badge/OpenRouter-94A3B8?logo=openrouter&logoColor=fff)](#)
[![TikTok](https://img.shields.io/badge/TikTok-black?logo=tiktok&logoColor=white)](#)
[![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?logo=YouTube&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)

tt2yt is a Python script that allows you to upload TikTok videos directly to YouTube Shorts. It uses the YouTube Data API to handle video uploads and metadata management.

## Features:

 - Upload TikTok videos to YouTube Shorts
 - Automatically set video title and description based on metadata and OpenRouter (optional)
 - Handles video processing and formatting for YouTube Shorts
 - Keeps track of uploaded videos to avoid duplicates through SQLite

## Requirements:

 - Python 3.x
 - Google API Client Library for Python
 - OpenRouter API key (Optional, for AI-generated descriptions)
 - Google Client Secrets JSON file for YouTube API authentication

## Installation:

1. Clone the repository:
   ```bash
   git clone https://github.com/proton0/tt2yt.git
   ```

> [!NOTE]
>
> If you want the latest features, you can run `git checkout experimental` to get experimental features.
>

2. Install the required dependencies and create the virtual environment:
   ```bash
   ./setup.sh
   ```

3. Set up Google API credentials:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project and enable the YouTube Data API v3.
    - Create OAuth 2.0 credentials and download the `client_secrets.json` file.
    - Add the Google email address of the YouTube channel you want to upload to in **Test Users** (mandatory for Google apps in testing).
    - Place the `client_secrets.json` file in the `secrets` directory.
    - Run the start script with your credentials to authenticate and generate the required secrets:
   
   ```bash
   # With OpenRouter AI descriptions:
   ./start.sh -t <TIKTOK USERNAME> -o <OPENROUTER API KEY> -c secrets/client_secrets.json

   # Without OpenRouter (falls back to original TikTok caption):
   ./start.sh -t <TIKTOK USERNAME> -c secrets/client_secrets.json
   ```

> [!NOTE]
>
> It is highly recommended to get an OpenRouter API Key, it is free and you can get it by just signing up for OpenRouter
>

4. Run tt2yt:
   ```bash
   ./start.sh
   ```

> [!NOTE]
> The script automatically handles OAuth access token refreshes while running, but if it has been stopped for a long time or credentials are revoked, you may need to re-run it interactively to sign in again.
>
> YouTube has a upload quota for the API (~6 per day) so uploads may fail!

## Credits:

- Developed by [proton0](https://github.com/proton0)

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
