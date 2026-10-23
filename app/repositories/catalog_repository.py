import sqlite3
import unicodedata
from pathlib import Path
from typing import Any


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return "".join(char for char in text.lower() if char.isalnum())


class CatalogRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.create_function("normalize", 1, normalize, deterministic=True)
        connection.create_collation(
            "PY_CASEFOLD",
            lambda left, right: (
                (left.casefold() > right.casefold())
                - (left.casefold() < right.casefold())
            ),
        )
        return connection

    @staticmethod
    def _in(values: list[Any], parameters: list[Any]) -> str:
        parameters.extend(values)
        return ", ".join("?" for _ in values)

    def filters(self, region: str = "BR") -> dict[str, list[Any]]:
        with self._connect() as connection:
            values = lambda sql, params=(): [
                row[0] for row in connection.execute(sql, params)
            ]

            return {
                "types": values(
                    """
                    SELECT DISTINCT a.type
                    FROM anime a
                    JOIN anime_regions ar ON ar.anime_id = a.id
                    WHERE ar.region = ?
                      AND a.type IS NOT NULL
                    ORDER BY a.type
                    """,
                    (region,),
                ),
                "availability_statuses": values(
                    """
                    SELECT DISTINCT availability_status
                    FROM anime_regions
                    WHERE region = ?
                      AND availability_status IS NOT NULL
                    ORDER BY availability_status
                    """,
                    (region,),
                ),
                "years": values(
                    """
                    SELECT DISTINCT a.year
                    FROM anime a
                    JOIN anime_regions ar ON ar.anime_id = a.id
                    WHERE ar.region = ?
                      AND a.year IS NOT NULL
                    ORDER BY a.year DESC
                    """,
                    (region,),
                ),
                "maturity_ratings": values(
                    """
                    SELECT DISTINCT maturity_rating
                    FROM anime_regions
                    WHERE region = ?
                      AND maturity_rating IS NOT NULL
                    ORDER BY maturity_rating
                    """,
                    (region,),
                ),
                "content_descriptors": values(
                    """
                    SELECT DISTINCT descriptor
                    FROM anime_region_content_descriptors arcd
                    JOIN anime_regions ar
                        ON ar.id = arcd.anime_region_id
                    WHERE ar.region = ?
                    ORDER BY descriptor
                    """,
                    (region,),
                ),
                "audio_locales": values(
                    """
                    SELECT DISTINCT locale
                    FROM anime_region_audio_locales aral
                    JOIN anime_regions ar
                        ON ar.id = aral.anime_region_id
                    WHERE ar.region = ?
                      AND locale IS NOT NULL
                      AND locale != ''
                    ORDER BY locale
                    """,
                    (region,),
                ),
                "subtitle_locales": values(
                    """
                    SELECT DISTINCT locale
                    FROM anime_region_subtitle_locales arsl
                    JOIN anime_regions ar
                        ON ar.id = arsl.anime_region_id
                    WHERE ar.region = ?
                      AND locale IS NOT NULL
                      AND locale != ''
                    ORDER BY locale
                    """,
                    (region,),
                ),
                "tags": values(
                    """
                    SELECT name
                    FROM tags
                    ORDER BY name COLLATE PY_CASEFOLD
                    """
                ),
                "season_counts": values(
                    """
                    SELECT DISTINCT a.season_count
                    FROM anime a
                    JOIN anime_regions ar ON ar.anime_id = a.id
                    WHERE ar.region = ?
                      AND a.season_count IS NOT NULL
                    ORDER BY a.season_count
                    """,
                    (region,),
                ),
                "episode_counts": values(
                    """
                    SELECT DISTINCT a.episode_count
                    FROM anime a
                    JOIN anime_regions ar ON ar.anime_id = a.id
                    WHERE ar.region = ?
                      AND a.episode_count IS NOT NULL
                    ORDER BY a.episode_count
                    """,
                    (region,),
                ),
            }

    def explore_filters(self) -> dict[str, list[Any]]:
        with self._connect() as connection:
            values = lambda sql, params=(): [
                row[0] for row in connection.execute(sql, params)
            ]

            return {
                "types": values(
                    """
                    SELECT DISTINCT type
                    FROM anime
                    WHERE type IS NOT NULL
                    ORDER BY type
                    """
                ),
                "years": values(
                    """
                    SELECT DISTINCT year
                    FROM anime
                    WHERE year IS NOT NULL
                    ORDER BY year DESC
                    """
                ),
                "tags": values(
                    """
                    SELECT name
                    FROM tags
                    ORDER BY name COLLATE PY_CASEFOLD
                    """
                ),
                "season_counts": values(
                    """
                    SELECT DISTINCT season_count
                    FROM anime
                    WHERE season_count IS NOT NULL
                    ORDER BY season_count
                    """
                ),
                "episode_counts": values(
                    """
                    SELECT DISTINCT episode_count
                    FROM anime
                    WHERE episode_count IS NOT NULL
                    ORDER BY episode_count
                    """
                ),
            }

    def tags_payload(self) -> dict[str, list[Any]]:
        return {"tags": self.filters()["tags"]}

    def search(
        self,
        filters: dict[str, Any],
        region: str = "BR",
    ) -> tuple[list[dict[str, Any]], int]:
        where: list[str] = [
            "ar.region = ?",
        ]
        parameters: list[Any] = [region]

        query = normalize(filters.get("q"))

        selected_tags = list(
            dict.fromkeys(
                normalize(str(x))
                for x in filters.get("tags") or []
            )
        )

        selected_descriptors = list(
            dict.fromkeys(
                normalize(str(x))
                for x in filters.get("content_descriptor") or []
            )
        )

        if query:
            where.append(
                """
                instr(
                    normalize(
                        COALESCE(ar.title, '') || ' ' ||
                        COALESCE(ar.promo_title, '') || ' ' ||
                        COALESCE(ar.description, '') || ' ' ||
                        COALESCE(a.slug_title, '') || ' ' ||
                        COALESCE(
                            (
                                SELECT group_concat(t.name, ' ')
                                FROM anime_tags at
                                JOIN tags t ON t.id = at.tag_id
                                WHERE at.anime_id = a.id
                            ),
                            ''
                        )
                    ),
                    ?
                ) > 0
                """
            )
            parameters.append(query)

        if filters.get("type"):
            where.append("a.type = ?")
            parameters.append(filters["type"])

        if filters.get("availability_status"):
            where.append("ar.availability_status = ?")
            parameters.append(filters["availability_status"])

        if filters.get("year"):
            where.append(
                f"a.year IN ({self._in(list(filters['year']), parameters)})"
            )

        if filters.get("maturity_rating"):
            where.append(
                f"""
                ar.maturity_rating IN (
                    {self._in(list(filters["maturity_rating"]), parameters)}
                )
                """
            )

        if filters.get("audio_locale"):
            audio_locales = list(
                dict.fromkeys(filters["audio_locale"])
            )
            placeholders = self._in(audio_locales, parameters)

            where.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM anime_region_audio_locales aral
                    WHERE aral.anime_region_id = ar.id
                      AND aral.locale IN ({placeholders})
                )
                """
            )

        if filters.get("subtitle_locale"):
            subtitle_locales = list(
                dict.fromkeys(filters["subtitle_locale"])
            )
            placeholders = self._in(subtitle_locales, parameters)

            where.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM anime_region_subtitle_locales arsl
                    WHERE arsl.anime_region_id = ar.id
                      AND arsl.locale IN ({placeholders})
                )
                """
            )

        if filters.get("user_status"):
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM user_anime ua
                    WHERE ua.user_id = 1
                      AND ua.anime_id = a.id
                      AND ua.status = ?
                )
                """
            )
            parameters.append(filters["user_status"])

        for column, key in (
            ("ar.rating_average", "min_rating"),
            ("a.season_count", "season_count_min"),
            ("a.episode_count", "episode_count_min"),
        ):
            if filters.get(key) is not None:
                where.append(f"{column} >= ?")
                parameters.append(filters[key])

        if selected_tags:
            placeholders = self._in(selected_tags, parameters)

            where.append(
                """
                a.id IN (
                    SELECT at.anime_id
                    FROM anime_tags at
                    JOIN tags t ON t.id = at.tag_id
                    WHERE normalize(t.name) IN ({})
                    GROUP BY at.anime_id
                    HAVING COUNT(DISTINCT normalize(t.name)) = ?
                )
                """.format(placeholders)
            )

            parameters.append(len(selected_tags))

        if selected_descriptors:
            placeholders = self._in(selected_descriptors, parameters)

            where.append(
                """
                ar.id IN (
                    SELECT arcd.anime_region_id
                    FROM anime_region_content_descriptors arcd
                    WHERE normalize(arcd.descriptor) IN ({})
                    GROUP BY arcd.anime_region_id
                    HAVING COUNT(DISTINCT normalize(arcd.descriptor)) = ?
                )
                """.format(placeholders)
            )

            parameters.append(len(selected_descriptors))

        condition = " AND ".join(where) or "1 = 1"

        sort = filters.get("sort", "relevance")
        query_terms = query.split()

        order_by, order_parameters = self._order_by(
            sort,
            query,
            query_terms,
        )

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 25)

        with self._connect() as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM anime a
                JOIN anime_regions ar ON ar.anime_id = a.id
                WHERE {condition}
                """,
                parameters,
            ).fetchone()[0]

            rows = connection.execute(
                f"""
                SELECT
                    a.*,
                    ar.id AS anime_region_id,
                    ar.region,
                    ar.title,
                    ar.description,
                    ar.promo_title,
                    ar.availability_status,
                    ar.rating_average,
                    ar.rating_total,
                    ar.maturity_rating,
                    ar.is_dubbed,
                    ar.is_subbed,
                    ar.is_mature,
                    ar.is_simulcast,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                          AND type = 'poster_tall'
                        ORDER BY ABS(COALESCE(width, 0) - 480), id
                        LIMIT 1
                    ) AS card_image,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                          AND type = 'poster_wide'
                        ORDER BY ABS(COALESCE(width, 0) - 1200), id
                        LIMIT 1
                    ) AS hero_image,

                    COALESCE(
                        (
                            SELECT group_concat(t.name, char(31))
                            FROM anime_tags at
                            JOIN tags t ON t.id = at.tag_id
                            WHERE at.anime_id = a.id
                        ),
                        ''
                    ) AS tags

                FROM anime a
                JOIN anime_regions ar ON ar.anime_id = a.id
                WHERE {condition}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                [
                    *parameters,
                    *order_parameters,
                    page_size,
                    (page - 1) * page_size,
                ],
            ).fetchall()

        return [self._card(dict(row)) for row in rows], total

    def explore(
        self,
        filters: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], int]:
        """Search the global catalog, returning one card per anime."""
        where: list[str] = []
        parameters: list[Any] = []

        query = normalize(filters.get("q"))

        selected_tags = list(
            dict.fromkeys(
                normalize(str(x))
                for x in filters.get("tags") or []
            )
        )

        if query:
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM anime_regions ar_search
                    WHERE ar_search.anime_id = a.id
                    AND instr(
                        normalize(
                            COALESCE(ar_search.title, '') || ' ' ||
                            COALESCE(ar_search.promo_title, '') || ' ' ||
                            COALESCE(ar_search.description, '') || ' ' ||
                            COALESCE(a.slug_title, '')
                        ),
                        ?
                    ) > 0
                )
                """
            )
            parameters.append(query)

        if filters.get("type"):
            where.append("a.type = ?")
            parameters.append(filters["type"])

        if filters.get("year"):
            where.append(
                f"a.year IN ({self._in(list(filters['year']), parameters)})"
            )

        if filters.get("season_count_min") is not None:
            where.append("a.season_count >= ?")
            parameters.append(filters["season_count_min"])

        if filters.get("episode_count_min") is not None:
            where.append("a.episode_count >= ?")
            parameters.append(filters["episode_count_min"])

        if selected_tags:
            placeholders = self._in(selected_tags, parameters)

            where.append(
                """
                a.id IN (
                    SELECT at.anime_id
                    FROM anime_tags at
                    JOIN tags t ON t.id = at.tag_id
                    WHERE normalize(t.name) IN ({})
                    GROUP BY at.anime_id
                    HAVING COUNT(DISTINCT normalize(t.name)) = ?
                )
                """.format(placeholders)
            )

            parameters.append(len(selected_tags))

        condition = " AND ".join(where) or "1 = 1"

        sort = filters.get("sort", "relevance")
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 25)

        if sort == "title_desc":
            order_by = (
                "display_ar.title COLLATE PY_CASEFOLD DESC, a.id"
            )
            order_parameters: list[Any] = []

        elif sort == "rating_desc":
            order_by = """
                display_ar.rating_average IS NULL,
                display_ar.rating_average DESC,
                display_ar.title COLLATE PY_CASEFOLD,
                a.id
            """
            order_parameters = []

        elif sort == "rating_asc":
            order_by = """
                display_ar.rating_average IS NOT NULL DESC,
                display_ar.rating_average ASC,
                display_ar.title COLLATE PY_CASEFOLD,
                a.id
            """
            order_parameters = []

        elif sort == "year_desc":
            order_by = """
                a.year IS NULL,
                a.year DESC,
                display_ar.title COLLATE PY_CASEFOLD,
                a.id
            """
            order_parameters = []

        elif sort == "year_asc":
            order_by = """
                a.year IS NOT NULL DESC,
                a.year ASC,
                display_ar.title COLLATE PY_CASEFOLD,
                a.id
            """
            order_parameters = []

        elif sort == "relevance" and query:
            order_by = """
                normalize(display_ar.title) != ?,
                NOT (normalize(display_ar.title) LIKE ? || '%'),
                display_ar.title COLLATE PY_CASEFOLD,
                a.id
            """
            order_parameters = [query, query]

        else:
            order_by = (
                "display_ar.title COLLATE PY_CASEFOLD, a.id"
            )
            order_parameters = []

        with self._connect() as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM anime a
                WHERE {condition}
                """,
                parameters,
            ).fetchone()[0]

            rows = connection.execute(
                f"""
                SELECT
                    a.id,
                    a.slug_title,
                    a.type,
                    a.year,
                    a.episode_count,
                    a.season_count,
                    a.last_public,

                    display_ar.title,
                    display_ar.description,
                    display_ar.promo_title,
                    display_ar.availability_status,
                    display_ar.rating_average,
                    display_ar.rating_total,
                    display_ar.maturity_rating,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                        AND type = 'poster_tall'
                        ORDER BY ABS(COALESCE(width, 0) - 480), id
                        LIMIT 1
                    ) AS card_image,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                        AND type = 'poster_wide'
                        ORDER BY ABS(COALESCE(width, 0) - 1200), id
                        LIMIT 1
                    ) AS hero_image,

                    COALESCE(
                        (
                            SELECT group_concat(t.name, char(31))
                            FROM anime_tags at
                            JOIN tags t ON t.id = at.tag_id
                            WHERE at.anime_id = a.id
                        ),
                        ''
                    ) AS tags,

                    (
                        SELECT group_concat(region, char(31))
                        FROM (
                            SELECT region
                            FROM anime_regions
                            WHERE anime_id = a.id
                            ORDER BY region
                        )
                    ) AS regions

                FROM anime a

                JOIN anime_regions display_ar
                    ON display_ar.id = (
                        SELECT ar_display.id
                        FROM anime_regions ar_display
                        WHERE ar_display.anime_id = a.id
                        ORDER BY
                            CASE
                                WHEN ar_display.region = 'US' THEN 0
                                ELSE 1
                            END,
                            ar_display.region
                        LIMIT 1
                    )

                WHERE {condition}

                ORDER BY {order_by}

                LIMIT ? OFFSET ?
                """,
                [
                    *parameters,
                    *order_parameters,
                    page_size,
                    (page - 1) * page_size,
                ],
            ).fetchall()

        items = []

        for row in rows:
            item = self._card(dict(row))

            item["regions"] = [
                region
                for region in (row["regions"] or "").split(chr(31))
                if region
            ]

            items.append(item)

        return items, total
    @staticmethod
    def _order_by(
        sort: str,
        query: str,
        terms: list[str],
    ) -> tuple[str, list[Any]]:
        if sort == "title_desc":
            return "ar.title COLLATE PY_CASEFOLD DESC, a.id", []

        if sort == "rating_desc":
            return (
                """
                ar.rating_average IS NULL,
                ar.rating_average DESC,
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [],
            )

        if sort == "rating_asc":
            return (
                """
                ar.rating_average IS NOT NULL DESC,
                ar.rating_average ASC,
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [],
            )

        if sort == "year_desc":
            return (
                """
                a.year IS NULL,
                a.year DESC,
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [],
            )

        if sort == "year_asc":
            return (
                """
                a.year IS NOT NULL DESC,
                a.year ASC,
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [],
            )

        if sort == "recently_published":
            return (
                """
                a.last_public DESC,
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [],
            )

        if sort == "relevance" and query:
            score = " + ".join(
                "instr(normalize(ar.title), ?) > 0"
                for _ in terms
            ) or "0"

            return (
                f"""
                normalize(ar.title) != ?,
                NOT (normalize(ar.title) LIKE ? || '%'),
                -({score}),
                ar.title COLLATE PY_CASEFOLD,
                a.id
                """,
                [query, query, *terms],
            )

        return "ar.title COLLATE PY_CASEFOLD, a.id", []

    def detail(
        self,
        anime_id: str,
        region: str = "BR",
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    a.*,
                    ar.id AS anime_region_id,
                    ar.region,
                    ar.title,
                    ar.description,
                    ar.promo_title,
                    ar.availability_status,
                    ar.rating_average,
                    ar.rating_total,
                    ar.maturity_rating,
                    ar.is_dubbed,
                    ar.is_subbed,
                    ar.is_mature,
                    ar.is_simulcast
                FROM anime a
                JOIN anime_regions ar
                    ON ar.anime_id = a.id
                   AND ar.region = ?
                WHERE a.id = ?
                """,
                (region, anime_id),
            ).fetchone()

            if not row:
                return None

            images = [
                dict(image)
                for image in connection.execute(
                    """
                    SELECT type, url, width, height
                    FROM anime_images
                    WHERE anime_id = ?
                    ORDER BY type, width, id
                    """,
                    (anime_id,),
                )
            ]

            tags = [
                tag[0]
                for tag in connection.execute(
                    """
                    SELECT t.name
                    FROM anime_tags at
                    JOIN tags t ON t.id = at.tag_id
                    WHERE at.anime_id = ?
                    ORDER BY t.name COLLATE PY_CASEFOLD
                    """,
                    (anime_id,),
                )
            ]

            descriptors = [
                descriptor[0]
                for descriptor in connection.execute(
                    """
                    SELECT descriptor
                    FROM anime_region_content_descriptors
                    WHERE anime_region_id = ?
                    ORDER BY descriptor
                    """,
                    (row["anime_region_id"],),
                )
            ]

            audio_locales = [
                locale[0]
                for locale in connection.execute(
                    """
                    SELECT locale
                    FROM anime_region_audio_locales
                    WHERE anime_region_id = ?
                    ORDER BY locale
                    """,
                    (row["anime_region_id"],),
                )
            ]

            subtitle_locales = [
                locale[0]
                for locale in connection.execute(
                    """
                    SELECT locale
                    FROM anime_region_subtitle_locales
                    WHERE anime_region_id = ?
                    ORDER BY locale
                    """,
                    (row["anime_region_id"],),
                )
            ]

        return self._detail(
            dict(row),
            images,
            tags,
            descriptors,
            audio_locales,
            subtitle_locales,
        )

    @staticmethod
    def _card(row: dict[str, Any]) -> dict[str, Any]:
        tags, maturity = (
            [
                tag
                for tag in row.pop("tags", "").split(chr(31))
                if tag
            ],
            row["maturity_rating"],
        )

        return {
            "id": row["id"],
            "title": row["title"],
            "slug_title": row["slug_title"] or "",
            "description": row["description"] or "",
            "promo_title": row["promo_title"] or "",
            "type": row["type"],
            "year": row["year"],
            "episodes": row["episode_count"],
            "seasons": row["season_count"],
            "availability_status": row["availability_status"],
            "maturity_rating": maturity,
            "genres": tags,
            "rating": row["rating_average"],
            "rating_total": row["rating_total"],
            "card_image": row["card_image"],
            "hero_image": row["hero_image"],
            "maturity_label": maturity,
            "maturity_icon": (
                f"/static/icons/maturity/{maturity}.svg"
                if maturity
                else None
            ),
        }

    @classmethod
    def _detail(
        cls,
        row: dict[str, Any],
        images: list[dict[str, Any]],
        tags: list[str],
        descriptors: list[str],
        audio_locales: list[str],
        subtitle_locales: list[str],
    ) -> dict[str, Any]:
        image_map: dict[str, list[dict[str, Any]]] = {}

        for image in images:
            image_map.setdefault(image["type"], []).append(image)

        card = cls._card(
            {
                **row,
                "tags": chr(31).join(tags),
                "card_image": cls._best_image(
                    images,
                    "poster_tall",
                    480,
                ),
                "hero_image": cls._best_image(
                    images,
                    "poster_wide",
                    1200,
                ),
            }
        )

        return {
            "id": row["id"],
            "title": row["title"],
            "slug_title": row["slug_title"],
            "description": row["description"],
            "promo_title": row["promo_title"],
            "type": row["type"],
            "last_public": row["last_public"],
            "images": image_map,
            "rating": {
                "average": row["rating_average"],
                "total": row["rating_total"],
            },
            "series_metadata": {
                "series_launch_year": row["year"],
                "episode_count": row["episode_count"],
                "season_count": row["season_count"],
                "availability_status": row["availability_status"],
                "maturity_rating": row["maturity_rating"],
                "is_dubbed": row["is_dubbed"],
                "is_subbed": row["is_subbed"],
                "is_mature": row["is_mature"],
                "is_simulcast": row["is_simulcast"],
                "tenant_categories": tags,
                "content_descriptors": descriptors,
                "audio_locales": audio_locales,
                "subtitle_locales": subtitle_locales,
            },
            "catalog_context": {
                **card,
                "region": row["region"],
            },
        }

    @staticmethod
    def _best_image(
        images: list[dict[str, Any]],
        image_type: str,
        target: int,
    ) -> str | None:
        candidates = [
            image for image in images
            if image["type"] == image_type
        ]

        return (
            min(
                candidates,
                key=lambda image: abs(
                    (image["width"] or 0) - target
                ),
            )["url"]
            if candidates
            else None
        )

    def set_user_anime(
        self,
        user_id: int,
        anime_id: str,
        status: str,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO user_anime (user_id, anime_id, status)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, anime_id)
                DO UPDATE SET status = excluded.status
                """,
                (user_id, anime_id, status),
            )

            row = connection.execute(
                """
                SELECT user_id, anime_id, status
                FROM user_anime
                WHERE user_id = ? AND anime_id = ?
                """,
                (user_id, anime_id),
            ).fetchone()

        return dict(row)

    def delete_user_anime(
        self,
        user_id: int,
        anime_id: str,
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM user_anime
                WHERE user_id = ? AND anime_id = ?
                """,
                (user_id, anime_id),
            )

            return cursor.rowcount > 0

    def user_anime(
        self,
        user_id: int,
        status: str | None = None,
        region: str = "BR",
    ) -> list[dict[str, Any]]:
        where = [
            "ua.user_id = ?",
            "ar.region = ?",
        ]
        parameters: list[Any] = [user_id, region]

        if status:
            where.append("ua.status = ?")
            parameters.append(status)

        condition = " AND ".join(where)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    a.id,
                    ua.status,

                    a.slug_title,
                    a.type,
                    a.year,
                    a.episode_count,
                    a.season_count,

                    ar.title,
                    ar.description,
                    ar.promo_title,
                    ar.availability_status,
                    ar.maturity_rating,
                    ar.rating_average,
                    ar.rating_total,
                    ar.is_simulcast,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                          AND type = 'poster_tall'
                        ORDER BY ABS(COALESCE(width, 0) - 480), id
                        LIMIT 1
                    ) AS card_image,

                    (
                        SELECT url
                        FROM anime_images
                        WHERE anime_id = a.id
                          AND type = 'poster_wide'
                        ORDER BY ABS(COALESCE(width, 0) - 1200), id
                        LIMIT 1
                    ) AS hero_image,

                    COALESCE(
                        (
                            SELECT group_concat(t.name, char(31))
                            FROM anime_tags at
                            JOIN tags t ON t.id = at.tag_id
                            WHERE at.anime_id = a.id
                        ),
                        ''
                    ) AS tags

                FROM user_anime ua
                JOIN anime a
                    ON a.id = ua.anime_id
                JOIN anime_regions ar
                    ON ar.anime_id = a.id
                   AND ar.region = ?
                WHERE {condition}
                ORDER BY ar.title COLLATE PY_CASEFOLD, a.id
                """,
                [region, *parameters],
            ).fetchall()

        return [
            self._card(dict(row))
            | {
                "anime_id": row["id"],
                "status": row["status"],
            }
            for row in rows
        ]

    def get_user_by_username(
        self,
        username: str,
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        return dict(row) if row else None

    def create_user(
        self,
        username: str,
        password_hash: str,
    ) -> int | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                ON CONFLICT(username) DO NOTHING
                """,
                (username, password_hash),
            )

        return cursor.lastrowid if cursor.rowcount else None