from pathlib import Path
from typing import Any

from app.repositories.catalog_repository import CatalogRepository


class CatalogService:
    """Application-facing facade for the normalized anime-data database."""

    def __init__(self, database_path: Path):
        self.repository = CatalogRepository(database_path)

    def categories_payload(self) -> dict[str, list[str]]:
        return {"tags": self.repository.filters()["tags"]}

    def filters(self, region: str = "BR") -> dict[str, list[Any]]:
        return self.repository.filters(region=region)

    def explore_filters(self) -> dict[str, list[Any]]:
        return self.repository.explore_filters()

    def search(
        self,
        region: str = "BR",
        **filters: Any,
    ) -> tuple[list[dict[str, Any]], int]:
        return self.repository.search(
            filters=filters,
            region=region,
        )

    def explore(
        self,
        **filters: Any,
    ) -> tuple[list[dict[str, Any]], int]:
        return self.repository.explore(
            filters=filters,
        )

    def detail(
        self,
        anime_id: str,
        region: str = "BR",
    ) -> dict[str, Any] | None:
        return self.repository.detail(
            anime_id=anime_id,
            region=region,
        )

    def set_user_anime(
        self,
        user_id: int,
        anime_id: str,
        status: str,
    ) -> dict[str, Any]:
        return self.repository.set_user_anime(
            user_id=user_id,
            anime_id=anime_id,
            status=status,
        )

    def delete_user_anime(
        self,
        user_id: int,
        anime_id: str,
    ) -> bool:
        return self.repository.delete_user_anime(
            user_id=user_id,
            anime_id=anime_id,
        )

    def user_anime(
        self,
        user_id: int,
        status: str | None = None,
        region: str = "BR",
    ) -> list[dict[str, Any]]:
        return self.repository.user_anime(
            user_id=user_id,
            status=status,
            region=region,
        )

    def get_user_by_username(
        self,
        username: str,
    ) -> dict[str, Any] | None:
        return self.repository.get_user_by_username(username)

    def create_user(
        self,
        username: str,
        password_hash: str,
    ) -> int | None:
        return self.repository.create_user(username, password_hash)