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

2. Set up Google API credentials:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project and enable the YouTube Data API v3.
    - Create OAuth 2.0 credentials and download the `client_secrets.json` file.
    - Add the Google email address of the YouTube channel you want to upload to in **Test Users** (mandatory for Google apps in testing).
    - Place the `client_secrets.json` file in the `secrets` directory.
    - Run the start script with your credentials to authenticate and generate the required secrets:
   
   ```bash
   # With OpenRouter AI descriptions:
   ./start.sh -t <TIKTOK PROFILE> -tc <TIKTOK CHANNEL ID> -o <OPENROUTER API KEY> -d <DISCORD WEBHOOK URL "OPTIONAL"> -c secrets/client_secrets.json

   # Without OpenRouter (falls back to original TikTok caption):
   ./start.sh -t <TIKTOK PROFILE> -tc <TIKTOK CHANNEL ID> -d <DISCORD WEBHOOK URL "OPTIONAL"> -c secrets/client_secrets.json
   ```

> [!NOTE]
>
> It is highly recommended to get an OpenRouter API Key, it is free and you can get it by just signing up for OpenRouter
>
> You can get your channel ID by running `yt-dlp --print channel_id <A video you posted>`
> 
> Example: `yt-dlp --print channel_id https://www.tiktok.com/@vproton0/video/7666384110281215252`
> 
> If you dont want to do this, you can just remove the `-tc` flag but
> it is a LOT better to give channel ID as TikTok may block yt-dlp from scraping your profile

3. Run tt2yt:
   ```bash
   ./start.sh
   ```

> [!NOTE]
> The script automatically handles OAuth access token refreshes while running, but if it has been stopped for a long time or credentials are revoked, you may need to re-run it interactively to sign in again.
>
> YouTube has a upload quota for the API (~6 per day) so uploads may fail!

## Docker Support

Follow the installation and instead of running `start.sh`, run the following commands

1. Build the Docker image:
   ```bash
   docker build -t tt2yt .
   ```

2. Set up the Docker container:
   ```bash
    docker compose run -it --rm -v $(pwd)/secrets:/app/secrets tt2yt -tc <TIKTOK CHANNEL ID> -o <OPENROUTER API KEY> -d <DISCORD WEBHOOK URL "OPTIONAL"> -c secrets/client_secrets.json
   ```

## Credits:

- Developed by [proton0](https://github.com/proton0)

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
