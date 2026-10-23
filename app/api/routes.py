from typing import Annotated, Literal

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.source_data import UserAnimeRequest
from app.security import hash_password, verify_password
from app.services.catalog_service import CatalogService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


def service(request: Request) -> CatalogService:
    return request.app.state.catalog


def current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(401, "Usuário não autenticado")

    return int(user_id)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None,
            "register_error": None,
            "open_register": False,
        },
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = service(request).get_user_by_username(username.strip())

    if not user or not verify_password(
        password,
        user["password_hash"],
    ):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Usuário ou senha inválidos.",
            },
            status_code=401,
        )

    request.session["user_id"] = user["id"]

    return RedirectResponse("/", status_code=303)


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    username = username.strip()
    if not username or not password:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": None,
                "register_error": "Informe um usuário e uma senha.",
                "open_register": True,
            },
            status_code=400,
        )

    user_id = service(request).create_user(
        username,
        hash_password(password),
    )
    if user_id is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": None,
                "register_error": "Este usuário já está cadastrado.",
                "open_register": True,
            },
            status_code=409,
        )

    request.session["user_id"] = user_id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/watched", response_class=HTMLResponse)
def watched(request: Request):
    return templates.TemplateResponse(
        request,
        "user_list.html",
        {"title": "Assistidos", "status": "watched"},
    )


@router.get("/watch-later", response_class=HTMLResponse)
def watch_later(request: Request):
    return templates.TemplateResponse(
        request,
        "user_list.html",
        {"title": "Para assistir", "status": "watch_later"},
    )


@router.get("/anime/{anime_id}", response_class=HTMLResponse)
def anime_page(
    request: Request,
    anime_id: str,
    region: str = "BR",
):
    anime = service(request).detail(
        anime_id=anime_id,
        region=region,
    )

    if not anime:
        raise HTTPException(404, "Anime não encontrado")

    return templates.TemplateResponse(
        request,
        "anime_detail.html",
        {"anime": anime},
    )


@router.get("/api/categories")
def categories(request: Request):
    return service(request).categories_payload()


@router.get("/api/filters")
def filters(
    request: Request,
    region: str = "BR",
):
    return service(request).filters(region=region)


@router.get("/api/animes")
def animes(
    request: Request,
    region: str = "BR",
    q: str | None = None,
    type: str | None = None,
    availability_status: str | None = None,
    year: Annotated[list[int] | None, Query()] = None,
    min_rating: Annotated[float | None, Query(ge=0, le=5)] = None,
    maturity_rating: Annotated[list[str] | None, Query()] = None,
    tags: Annotated[list[str] | None, Query()] = None,
    audio_locale: Annotated[list[str] | None, Query()] = None,
    subtitle_locale: Annotated[list[str] | None, Query()] = None,
    content_descriptor: Annotated[list[str] | None, Query()] = None,
    season_count_min: Annotated[int | None, Query(ge=0)] = None,
    episode_count_min: Annotated[int | None, Query(ge=0)] = None,
    user_status: Literal["watched", "watch_later"] | None = None,
    sort: Literal[
        "relevance",
        "title_asc",
        "title_desc",
        "rating_desc",
        "rating_asc",
        "year_desc",
        "year_asc",
        "recently_published",
    ] = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 25,
):
    items, total = service(request).search(
        region=region,
        q=q,
        type=type,
        availability_status=availability_status,
        year=year,
        min_rating=min_rating,
        maturity_rating=maturity_rating,
        tags=tags,
        audio_locale=audio_locale,
        subtitle_locale=subtitle_locale,
        content_descriptor=content_descriptor,
        season_count_min=season_count_min,
        episode_count_min=episode_count_min,
        user_status=user_status,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next_page": page * page_size < total,
        },
    }


@router.get("/explore", response_class=HTMLResponse)
def explore_page(request: Request):
    return templates.TemplateResponse(
        request,
        "explore.html",
    )

@router.get("/api/explore/filters")
def explore_filters(request: Request):
    return service(request).explore_filters()

@router.get("/api/explore")
def explore(
    request: Request,
    q: str | None = None,
    sort: Literal[
        "relevance",
        "title_asc",
        "title_desc",
        "rating_desc",
        "rating_asc",
        "year_desc",
        "year_asc",
    ] = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 25,
    type: str | None = None,
    year: list[int] | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
    season_count_min: int | None = Query(default=None, ge=0),
    episode_count_min: int | None = Query(default=None, ge=0),
):
    items, total = service(request).explore(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        type=type,
        year=year,
        tags=tags,
        season_count_min=season_count_min,
        episode_count_min=episode_count_min,
    )

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next_page": page * page_size < total,
        },
    }

@router.get("/api/animes/{anime_id}")
def anime(
    request: Request,
    anime_id: str,
    region: str = "BR",
):
    item = service(request).detail(
        anime_id=anime_id,
        region=region,
    )

    if not item:
        raise HTTPException(404, "Anime não encontrado")

    return item


@router.post("/api/user/anime")
def set_user_anime(
    request: Request,
    payload: UserAnimeRequest,
):
    user_id = current_user_id(request)

    return service(request).set_user_anime(
        user_id=user_id,
        anime_id=payload.anime_id,
        status=payload.status,
    )


@router.delete("/api/user/anime/{anime_id}")
def delete_user_anime(
    request: Request,
    anime_id: str,
):
    user_id = current_user_id(request)

    return service(request).delete_user_anime(
        user_id=user_id,
        anime_id=anime_id,
    )


@router.get("/api/user/anime")
def user_anime(
    request: Request,
    status: str | None = None,
    region: str = "BR",
):
    user_id = current_user_id(request)

    return service(request).user_anime(
        user_id=user_id,
        status=status,
        region=region,
    )