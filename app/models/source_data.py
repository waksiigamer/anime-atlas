from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Category(SourceModel):
    id: str
    title: str


class Localization(SourceModel):
    title: str
    description: str | None = None
    locale: str | None = None


class Subcategory(SourceModel):
    id: str
    parent_category_id: str
    localization: Localization
    slug: str | None = None


class Collection(SourceModel):
    total: int | None = None
    data: list[Any] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class AnimeSource(SourceModel):
    id: str
    title: str | None = None
    description: str | None = None
    promo_title: str | None = None
    slug_title: str | None = None
    type: str | None = None
    images: dict[str, Any] = Field(default_factory=dict)
    series_metadata: dict[str, Any] = Field(default_factory=dict)
    rating: dict[str, Any] = Field(default_factory=dict)


class UserAnimeRequest(BaseModel):
    anime_id: str
    status: Literal["watched", "watch_later"]