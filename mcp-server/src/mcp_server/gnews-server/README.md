# gnews-server

MCP server (built with the high-level `MCPServer` interface, formerly `FastMCP`) exposing the [GNews API](https://docs.gnews.io/).

## Tools

- `search_news` — wraps [`/search`](https://docs.gnews.io/endpoints/search-endpoint): keyword search (`q`, required) with `lang`, `country`, `max`, `search_in`, `nullable`, `date_from`, `date_to`, `sortby`, `page`, `truncate`.
- `get_top_headlines` — wraps [`/top-headlines`](https://docs.gnews.io/endpoints/top-headlines-endpoint): trending news by `category` with optional `q`, `lang`, `country`, `max`, `nullable`, `date_from`, `date_to`, `page`, `truncate`.

## Configuration

Set your API key (get one at https://gnews.io) in the `GNEWS_API_KEY` environment variable.

## Run

```bash
uv run gnews-server
```

Example client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "gnews": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-server", "run", "gnews-server"],
      "env": { "GNEWS_API_KEY": "your-api-key" }
    }
  }
}
```
