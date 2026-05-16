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

import sqlite3
from pathlib import Path

DB_FILE = Path("secrets/upload_history.db")


class UploadTracker:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS uploads
                         (
                             tiktok_id
                             TEXT
                             PRIMARY
                             KEY,
                             youtube_id
                             TEXT,
                             uploaded_at
                             TIMESTAMP
                             DEFAULT
                             CURRENT_TIMESTAMP
                         )
                         """)
            conn.commit()

    def is_uploaded(self, tiktok_id: str) -> bool:
        print(f"Checking if video {tiktok_id} is uploaded")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM uploads WHERE tiktok_id = ?", (tiktok_id,))
            return cursor.fetchone() is not None

    def mark_as_uploaded(self, tiktok_id: str, youtube_id: str):
        print(f"Set {tiktok_id} as uploaded")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO uploads (tiktok_id, youtube_id) VALUES (?, ?)",
                (tiktok_id, youtube_id)
            )
            conn.commit()
