import sqlite3

import pytest

from app.repositories.catalog_repository import CatalogRepository


@pytest.fixture
def repository(tmp_path):
    database_path = tmp_path / "test.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # =====================================================
        # Catalog schema
        # =====================================================

        connection.executescript(
            """
            CREATE TABLE anime (
                id TEXT PRIMARY KEY,
                external_id TEXT,
                channel_id TEXT,
                title TEXT NOT NULL,
                slug_title TEXT,
                description TEXT,
                promo_title TEXT,
                type TEXT,
                year INTEGER,
                episode_count INTEGER,
                season_count INTEGER,
                availability_status TEXT,
                rating_average REAL,
                rating_total INTEGER,
                maturity_rating TEXT,
                is_dubbed BOOLEAN,
                is_subbed BOOLEAN,
                is_mature BOOLEAN,
                is_simulcast BOOLEAN,
                last_public TEXT
            );

            CREATE TABLE anime_images (
                id INTEGER PRIMARY KEY,
                anime_id TEXT NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                UNIQUE (anime_id, type, url)
            );

            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE anime_tags (
                anime_id TEXT NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id),
                PRIMARY KEY (anime_id, tag_id)
            );

            CREATE TABLE anime_content_descriptors (
                anime_id TEXT NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
                descriptor TEXT NOT NULL,
                PRIMARY KEY (anime_id, descriptor)
            );

            -- =================================================
            -- User schema
            -- =================================================

            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE
            );

            CREATE TABLE user_anime (
                user_id INTEGER NOT NULL,
                anime_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('watched', 'watch_later')
                ),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (user_id, anime_id),

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (anime_id) REFERENCES anime(id)
            );
            """
        )

        # User de teste
        connection.execute(
            """
            INSERT INTO users (id, username)
            VALUES (?, ?)
            """,
            (1, "test_user"),
        )

        # Anime de teste
        connection.execute(
            """
            INSERT INTO anime (
                id,
                title,
                slug_title,
                type,
                year
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ANIME001",
                "Anime Teste",
                "anime-teste",
                "series",
                2024,
            ),
        )

        connection.commit()

    return CatalogRepository(database_path)


def test_create_user_anime(repository):
    result = repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watched",
    )

    assert result == {
        "user_id": 1,
        "anime_id": "ANIME001",
        "status": "watched",
    }


def test_update_user_anime_status(repository):
    repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watched",
    )

    result = repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watch_later",
    )

    assert result == {
        "user_id": 1,
        "anime_id": "ANIME001",
        "status": "watch_later",
    }


def test_delete_user_anime(repository):
    repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watched",
    )

    result = repository.delete_user_anime(
        user_id=1,
        anime_id="ANIME001",
    )

    assert result is True

    assert repository.user_anime(user_id=1) == []


def test_user_anime_prevents_duplicates(repository):
    repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watched",
    )

    repository.set_user_anime(
        user_id=1,
        anime_id="ANIME001",
        status="watch_later",
    )

    items = repository.user_anime(user_id=1)

    assert len(items) == 1
    assert items[0]["anime_id"] == "ANIME001"
    assert items[0]["status"] == "watch_later"