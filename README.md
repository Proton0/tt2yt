# tt2yt: TikTok to YouTube Shorts Uploader

tt2yt is a Python script that allows you to upload TikTok videos directly to YouTube Shorts. It uses the YouTube Data API to handle video uploads and metadata management.

## Features:

 - Upload TikTok videos to YouTube Shorts
 - Automatically set video title and description based on metadata and OpenRouter
 - Handles video processing and formatting for YouTube Shorts
 - Keeps tracks of uploaded videos to avoid duplicates through SQLite

## Requirements:

 - Python 3.x
 - Google API Client Library for Python
 - OpenRouter API for the description (Supports **FREE** models)
 - Google Client Secrets JSON file for YouTube API authentication

## Installation:

1. Clone the repository:
   ```bash
   git clone https://github.com/proton0/tt2yt`

2. Install the required dependencies and create the virtual environment:
   `./setup.sh`

3. Set up Google API credentials:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project and enable the YouTube Data API v3.
    - Create OAuth 2.0 credentials and download the `client_secrets.json` file
    - Put your google account with the YouTube channel you want to upload to in Test Users
    - Place the `client_secrets.json` file in `secrets` directory
    - Run the script with your credentials to authenticate and generate the required secrets.
   
   `./setup.sh -t <TIKTOK USERNAME> -o <OPENROUTER API KEY> -c secrets/client_secrets.json`

4. Run tt2yt with `./launch.sh`

> [!NOTE]
> Do note, the token does expire so you will need to re-run tt2yt
>
> You do not need to run tt2yt like the above, just run it normally with `./launch.sh`
> and it should open up a browser window for you to login

## Credits:

    - Developed by [proton0](https://github.com/proton0)

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.