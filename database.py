import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "links.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            target_url TEXT NOT NULL UNIQUE,
            click_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    connection.commit()
    connection.close()