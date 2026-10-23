"""Validate the normalized SQLite source used by Anime Atlas."""

import argparse
import sqlite3
from pathlib import Path

REQUIRED_TABLES = {
    "anime",
    "anime_images",
    "tags",
    "anime_tags",
    "anime_content_descriptors",
}


def validate(database_path: Path) -> None:
    if not database_path.is_file():
        raise SystemExit(f"Banco não encontrado: {database_path}")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        missing = REQUIRED_TABLES - tables
        if missing:
            raise SystemExit(f"Schema incompleto; tabelas ausentes: {', '.join(sorted(missing))}")
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise SystemExit(f"Integridade referencial inválida: {foreign_key_errors}")
        count = connection.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    print(f"SQLite válido: {database_path} ({count} animes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    default_database = Path(__file__).resolve().parents[2] / "anime-data" / "anime-data.db"
    parser.add_argument("database", type=Path, nargs="?", default=default_database)
    validate(parser.parse_args().database)
