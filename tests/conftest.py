import sqlite3

import pytest

from app.services.catalog_service import CatalogService


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "anime.db"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE anime (id TEXT PRIMARY KEY, external_id TEXT, channel_id TEXT, title TEXT NOT NULL, slug_title TEXT, description TEXT, promo_title TEXT, type TEXT, year INTEGER, episode_count INTEGER, season_count INTEGER, availability_status TEXT, rating_average REAL, rating_total INTEGER, maturity_rating TEXT, is_dubbed BOOLEAN, is_subbed BOOLEAN, is_mature BOOLEAN, is_simulcast BOOLEAN, last_public TEXT);
            CREATE TABLE anime_images (id INTEGER PRIMARY KEY, anime_id TEXT NOT NULL, type TEXT NOT NULL, url TEXT NOT NULL, width INTEGER, height INTEGER);
            CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
            CREATE TABLE anime_tags (anime_id TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (anime_id, tag_id));
            CREATE TABLE anime_content_descriptors (anime_id TEXT NOT NULL, descriptor TEXT NOT NULL, PRIMARY KEY (anime_id, descriptor));
        """)
        connection.executemany(
            "INSERT INTO anime VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "A1",
                    "ext-1",
                    "crunchyroll",
                    "Ação Única",
                    "acao-unica",
                    "Uma aventura fantástica",
                    "Promo",
                    "series",
                    2025,
                    12,
                    1,
                    "available",
                    4.5,
                    20,
                    "14",
                    1,
                    1,
                    0,
                    1,
                    "2026-01-02T00:00:00Z",
                ),
                (
                    "A2",
                    "ext-2",
                    "crunchyroll",
                    "Outro",
                    "outro",
                    "Drama e ação",
                    "",
                    "series",
                    2024,
                    24,
                    2,
                    "available",
                    4.0,
                    10,
                    "12",
                    0,
                    1,
                    0,
                    0,
                    "2025-01-02T00:00:00Z",
                ),
                (
                    "A3",
                    "ext-3",
                    "crunchyroll",
                    "Drama",
                    "drama",
                    "",
                    "",
                    "series",
                    2024,
                    10,
                    1,
                    "unavailable",
                    3.0,
                    2,
                    "16",
                    0,
                    0,
                    1,
                    0,
                    "2024-01-02T00:00:00Z",
                ),
            ],
        )
        connection.executemany(
            "INSERT INTO tags (id, name) VALUES (?, ?)",
            [(1, "Action"), (2, "Adventure"), (3, "Drama")],
        )
        connection.executemany(
            "INSERT INTO anime_tags VALUES (?, ?)",
            [("A1", 1), ("A1", 2), ("A2", 1), ("A2", 3), ("A3", 3)],
        )
        connection.executemany(
            "INSERT INTO anime_content_descriptors VALUES (?, ?)",
            [("A1", "Violência"), ("A1", "Nudez"), ("A2", "Violência")],
        )
        connection.executemany(
            "INSERT INTO anime_images (anime_id, type, url, width, height) VALUES (?, ?, ?, ?, ?)",
            [("A1", "poster_tall", "tall", 480, 720), ("A1", "poster_wide", "wide", 1200, 675)],
        )
    return path


@pytest.fixture
def service(database_path):
    return CatalogService(database_path)
