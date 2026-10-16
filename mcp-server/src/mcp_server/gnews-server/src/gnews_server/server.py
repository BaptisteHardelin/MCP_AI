from __future__ import annotations

import logging
import os
from typing import Annotated, Any, Literal

import httpx
from pydantic import Field

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

GNEWS_BASE_URL = "https://gnews.io/api/v4"
REQUEST_TIMEOUT_SECONDS = 15.0

# httpx logs full request URLs at INFO level, which would leak the API key.
logging.getLogger("httpx").setLevel(logging.WARNING)

mcp = MCPServer(
    "gnews_server",
    instructions=(
        "Search worldwide news articles and fetch trending top headlines through the GNews API. "
        "Use `search_news` for keyword queries and `get_top_headlines` for trending news by category."
    ),
)

Category = Literal[
    "general", "world", "nation", "business", "technology", "entertainment", "sports", "science", "health"
]
SortBy = Literal["publishedAt", "relevance"]

Query = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        description='Keywords to search for. Supports exact phrases ("...") and the AND, OR, NOT operators.',
    ),
]
Lang = Annotated[str | None, Field(description="Two-letter language code, e.g. 'en', 'fr', 'de'.")]
Country = Annotated[
    str | None, Field(description="Two-letter code of the publishing country, e.g. 'us', 'fr', 'gb'.")
]
Max = Annotated[int, Field(ge=1, le=100, description="Number of articles to return (upper limit depends on plan).")]
Page = Annotated[int, Field(ge=1, description="Page number; pagination cannot go beyond 1000 articles.")]
DateFrom = Annotated[
    str | None, Field(description="Earliest publication date, ISO 8601 (e.g. '2025-07-18T21:32:58Z').")
]
DateTo = Annotated[str | None, Field(description="Latest publication date, ISO 8601 (e.g. '2025-07-18T21:32:58Z').")]
Nullable = Annotated[
    list[Literal["description", "content", "image"]] | None,
    Field(description="Article fields allowed to be null in results."),
]
Truncate = Annotated[bool, Field(description="Truncate the article content field.")]

# Messages from https://docs.gnews.io/error-handling
ERROR_MESSAGES = {
    400: "Bad request: a parameter or the API key is missing or malformed.",
    401: "Unauthorized: the GNEWS_API_KEY does not match any account.",
    403: "Forbidden: the daily quota is exhausted (it resets at 00:00 UTC).",
    429: "Too many requests: the per-second rate limit was exceeded, retry later.",
    500: "GNews internal server error, retry later.",
    503: "GNews is temporarily offline for maintenance, retry later.",
}


def _get_api_key() -> str:
    api_key = os.environ.get("GNEWS_API_KEY")
    if not api_key:
        raise ToolError("GNEWS_API_KEY environment variable is not set.")
    return api_key


def _build_params(**params: Any) -> dict[str, str | int]:
    """Drop unset parameters and convert values to the format expected by GNews."""
    result: dict[str, str | int] = {}
    for key, value in params.items():
        if value is None or value is False or value == []:
            continue
        if isinstance(value, list):
            value = ",".join(value)
        result[key] = value
    return result


async def _call_gnews(endpoint: str, params: dict[str, str | int]) -> dict[str, Any]:
    params = {**params, "apikey": _get_api_key()}
    async with httpx.AsyncClient(base_url=GNEWS_BASE_URL, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            response = await client.get(endpoint, params=params)
        except httpx.HTTPError as exc:
            raise ToolError(f"Could not reach the GNews API: {exc.__class__.__name__}") from exc

    if response.is_error:
        detail = ERROR_MESSAGES.get(response.status_code, f"GNews API returned HTTP {response.status_code}.")
        try:
            errors = response.json().get("errors")
        except ValueError:
            errors = None
        if errors:
            detail = f"{detail} Details: {errors}"
        raise ToolError(detail)

    data = response.json()
    articles = data.get("articles", [])
    return {
        "total_articles": data.get("totalArticles", len(articles)),
        "count": len(articles),
        "articles": [
            {
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "url": article.get("url"),
                "image": article.get("image"),
                "published_at": article.get("publishedAt"),
                "language": article.get("lang"),
                "source": (article.get("source") or {}).get("name"),
                "source_url": (article.get("source") or {}).get("url"),
            }
            for article in articles
        ],
    }


@mcp.tool()
async def search_news(
    q: Query,
    lang: Lang = None,
    country: Country = None,
    max: Max = 10,
    search_in: Annotated[
        list[Literal["title", "description", "content"]] | None,
        Field(description="Article fields to search in. Defaults to title and description."),
    ] = None,
    nullable: Nullable = None,
    date_from: DateFrom = None,
    date_to: DateTo = None,
    sortby: Annotated[
        SortBy, Field(description="'publishedAt' (newest first) or 'relevance' (best keyword match first).")
    ] = "publishedAt",
    page: Page = 1,
    truncate: Truncate = False,
) -> dict[str, Any]:
    """Search news articles matching keywords using the GNews Search endpoint."""
    params = _build_params(
        q=q,
        lang=lang,
        country=country,
        max=max,
        nullable=nullable,
        sortby=sortby,
        page=page,
        **{"in": search_in, "from": date_from, "to": date_to, "truncate": "content" if truncate else None},
    )
    return await _call_gnews("/search", params)


@mcp.tool()
async def get_top_headlines(
    category: Annotated[Category, Field(description="Headline category.")] = "general",
    lang: Lang = None,
    country: Country = None,
    max: Max = 10,
    q: Annotated[
        str | None,
        Field(max_length=200, description="Optional keywords to filter headlines (supports AND, OR, NOT)."),
    ] = None,
    nullable: Nullable = None,
    date_from: DateFrom = None,
    date_to: DateTo = None,
    page: Page = 1,
    truncate: Truncate = False,
) -> dict[str, Any]:
    """Get current trending news articles using the GNews Top Headlines endpoint."""
    params = _build_params(
        category=category,
        lang=lang,
        country=country,
        max=max,
        q=q,
        nullable=nullable,
        page=page,
        **{"from": date_from, "to": date_to, "truncate": "content" if truncate else None},
    )
    return await _call_gnews("/top-headlines", params)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
