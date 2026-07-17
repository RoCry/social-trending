# Social Trending

Scheduled pipeline (GitHub Actions cron) that crawls trending discussions from social sources, enhances them with AI analysis, and publishes feed files to a GitHub release.

## Language

### Pipeline

**Crawler**:
A source-specific module that fetches trending stories and their discussion from one platform (Hacker News today; Reddit/Twitter planned) and produces Items.
_Avoid_: scraper, source client

**ContentFetcher**:
Extracts readable article content (text + HTML) from an Item's original URL, falling back across extraction strategies.
_Avoid_: base crawler, downloader

**Transformer**:
Enhances Items with Perspectives, deciding per Item whether one is needed or stale.
_Avoid_: enricher, AI enhancement step

**PerspectiveGenerator**:
Turns an Item's title and Comments into a Perspective via an LLM.
_Avoid_: LLM client, router

**Exporter**:
Renders Items into the published outputs: markdown digest, JSON Feed, raw JSON.
_Avoid_: renderer, formatter, output generation

**ItemStore**:
The cache of Items across runs. Reconciles freshly crawled Items with cached ones and persists results.
_Avoid_: database, cache layer

### Data

**Item**:
One trending story with its discussion, tracked across runs by a stable id. Carries source data, Comments, and an optional Perspective.
_Avoid_: story, post, entry

**Comment**:
One reader reaction to an Item: author plus content.

**Perspective**:
The AI analysis of an Item's discussion: title, summary, sentiment, and Viewpoints.
_Avoid_: summary (that's one field of it), insight

**Viewpoint**:
One consolidated opinion within a Perspective, with an approximate support percentage.
_Avoid_: opinion, stance

### Lifecycle

**Reconcile**:
Merging freshly crawled Items with cached ones: comments and timestamps update, the cached Perspective survives.
_Avoid_: merge with cache, dedupe

**Refresh**:
Regenerating an Item's Perspective because its discussion changed significantly since generation (comment-count thresholds).
_Avoid_: regenerate, invalidate
