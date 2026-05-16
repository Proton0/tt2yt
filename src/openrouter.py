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

import sys

import requests


class OpenRouter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate_description(self, title: str) -> str | None:
        print("Generating description")
        if not self.api_key:
            print("OpenRouter API key is missing.", file=sys.stderr)
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Proton0/tt2yt",
            "X-Title": "tt2yt YouTube Description Generator"
        }

        payload = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a YouTube SEO expert assistant. Your job is to generate short, "
                        "engaging video descriptions based on titles. Provide ONLY the final text "
                        "description block. Do not include any introductory remarks, explanations, "
                        "or meta-commentary like 'Here is your description'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Generate a short, viral YouTube description for a video titled: '{title}'"
                }
            ],
            "temperature": 0.7,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)

            response.raise_for_status()

            data = response.json()

            description = data["choices"][0]["message"]["content"].strip()

            print("Generated description")

            return description

        except requests.exceptions.RequestException as req_err:
            print(f"Network error calling OpenRouter API: {req_err}", file=sys.stderr)
            return None
        except (KeyError, IndexError, ValueError) as parse_err:
            print(f"Error parsing OpenRouter response payload: {parse_err}", file=sys.stderr)
            return None


if __name__ == "__main__":
    API_KEY = "you-aint-getting-my-api-key-lmao"
    ai = OpenRouter(API_KEY)
    desc = ai.generate_description("Building a bare-metal ESP32 OS from scratch!")
    print(f"\nGenerated Description Output:\n{desc}")
