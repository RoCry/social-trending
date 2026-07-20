# Social Trending

Scheduled pipeline that crawls trending discussions, extracts linked article content, optionally adds an LLM-generated
Perspective, and publishes a Markdown digest, JSON Feed, and raw JSON. Hacker News is the current source; source-specific
crawling and feed identity stay outside the reusable processing modules.

## Architecture

- **Crawler**: converts one social source into Items. `HackerNewsCrawler` receives its ContentFetcher.
- **ContentFetcher**: extracts article text and HTML through trafilatura, BeautifulSoup, then Jina. Sync work runs in a
  worker thread.
- **ItemStore**: reconciles fresh Items with SQLite state, preserves cached Perspectives, saves transformed Items, and
  removes stale state.
- **Transformer**: when enabled, applies Refresh policy and asks one PerspectiveGenerator when a Perspective is missing
  or stale.
- **PerspectiveGenerator**: owns prompt, smolllm configuration, XML-first response parsing, and fenced-JSON fallback.
- **Exporter**: pure rendering of Items into Markdown, JSON Feed, and raw JSON. Feed identity is supplied by the caller.

Pipeline: `crawl → reconcile → transform → save → export`.

## Configuration

```dotenv
ENABLE_LLM=false
SMOLLLM_MODEL=deepseek/deepseek-v4-flash
DEEPSEEK_API_KEY=key1,key2
# Optional
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
HN_COUNT=30
```

`SMOLLLM_MODEL` must use `provider/model` form. smolllm reads `{PROVIDER}_API_KEY` and optional
`{PROVIDER}_BASE_URL`; comma-separated keys/endpoints enable its native balancing.

LLM generation is disabled unless `ENABLE_LLM=true`. Scheduled GitHub Actions runs keep it disabled; manual dispatches
offer an opt-in checkbox.

## Run

```sh
uv sync --all-extras
uv run main.py
```

Enable paid Perspective generation explicitly:

```sh
ENABLE_LLM=true uv run main.py
```

Published artifacts:

- `cache/hackernews.md`
- `cache/hackernews.rss.json`
- `cache/hackernews.json`
- `cache/social.sqlite`

Tests are fully offline:

```sh
make test
```
