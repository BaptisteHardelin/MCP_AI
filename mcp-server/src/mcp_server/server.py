from __future__ import annotations

from mcp.server import MCPServer

mcp = MCPServer("documentation_database_server")

MOCK_DOCUMENTATION_DATABASE = [
    {
        "id": "doc-001",
        "title": "Authentication Overview",
        "category": "authentication",
        "summary": "Explains how users authenticate to the platform and manage session tokens.",
        "content": "Use OAuth 2.0 or API keys to authenticate requests. Tokens must be rotated every 90 days.",
        "tags": ["login", "oauth", "security"],
    },
    {
        "id": "doc-002",
        "title": "Customer API Guide",
        "category": "api",
        "summary": "Reference for calling the customer endpoints and handling pagination.",
        "content": "The customer API is versioned. Use the Accept header to request v1 or v2 responses.",
        "tags": ["customers", "api", "pagination"],
    },
    {
        "id": "doc-003",
        "title": "Database Deployment Checklist",
        "category": "deployment",
        "summary": "Checklist for migrating schema changes and validating production readiness.",
        "content": "Before deployment, run migrations, validate indexes, and confirm backup policies are active.",
        "tags": ["database", "migration", "deploy"],
    },
    {
        "id": "doc-004",
        "title": "Troubleshooting Rate Limits",
        "category": "troubleshooting",
        "summary": "Common reasons for 429 responses and recovery steps for clients.",
        "content": "When rate limited, retry with exponential backoff and inspect request quotas before resubmitting.",
        "tags": ["rate-limit", "errors", "retry"],
    },
]


@mcp.tool()
def get_documentation_from_database(
    query: str | None = None,
    limit: int = 5,
) -> dict:
    """Return documentation entries from a documentation database.

    Args:
        query: Optional keyword to filter documentation entries by title, category, or tag.
        limit: Maximum number of results to return.
    """
    filtered_documents = MOCK_DOCUMENTATION_DATABASE

    if query:
        normalized_query = query.strip().lower()
        filtered_documents = [
            document
            for document in filtered_documents
            if normalized_query in document["title"].lower()
            or normalized_query in document["category"].lower()
            or any(normalized_query in tag.lower() for tag in document["tags"])
        ]

    safe_limit = max(1, min(limit, len(filtered_documents) if filtered_documents else 1))
    result = filtered_documents[:safe_limit]

    return {
        "source": "mock_documentation_database",
        "count": len(result),
        "documents": result,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()