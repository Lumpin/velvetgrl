import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "velvetgrl.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            search_volume_estimate INTEGER DEFAULT 0,
            competition TEXT DEFAULT 'unknown',
            ad_value_score REAL DEFAULT 0.0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            published_at TEXT,
            pageviews INTEGER DEFAULT 0,
            pinterest_impressions INTEGER DEFAULT 0,
            pinterest_clicks INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_slug TEXT NOT NULL,
            image_path TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            board TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'pending',
            posted_at TEXT,
            impressions INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            FOREIGN KEY (post_slug) REFERENCES posts(slug)
        );

        CREATE TABLE IF NOT EXISTS calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week TEXT NOT NULL,
            post_data TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add any columns missing on existing databases (idempotent)."""
    pin_cols = {row[1] for row in conn.execute("PRAGMA table_info(pins)")}
    if "tags" not in pin_cols:
        conn.execute("ALTER TABLE pins ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'")
    if "pinterest_pin_id" not in pin_cols:
        conn.execute("ALTER TABLE pins ADD COLUMN pinterest_pin_id TEXT")
    if "metrics_updated_at" not in pin_cols:
        conn.execute("ALTER TABLE pins ADD COLUMN metrics_updated_at TEXT")
