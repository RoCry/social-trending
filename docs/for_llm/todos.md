# TODO

- [ ] using `hackernews` to get the top 10 stories(using 3 for testing) and root comments
- [ ] transformer.py to unify the format from sources
- [ ] cache_manager.py to cache above data in json file, put it in `cache` folder as using `{TODAY}_{source}.json`, we will restore and cache it in github action
- [ ] merge with cache, try figure out which fields needs regenerate with llm
- [ ] llm_processor.py base on litellm, using pydantic

final data structure will be like:
```json
{
    // original data
    "title": "title",
    "url": "url", // hn/reddit url, not the original url
    "content": "content", // optional, the original source content
    "comments": [
        {"content": "comment content", "author": "comment author"}
    ],
    "published_at": "2020-01-02T03:04:05Z", // optional
    /////////////////////////////
    "id": "id", // original id or generated id based on the url, for cache and deduplication with local db
    "created_at": "2025-01-10T09:51:07Z", // the fetched time
    "updated_at": "2025-01-10T09:51:07Z", // the last updated time, e.g. updated the comments
    // ai generated fields below
    "_summary": "the summary(the content of the url, title)", // won't regenerate
    "_generated_at_comment_count": 10, // the comment count when ai generate
    // optional, will regenerate if the comments changed a lot
    "_perspective": { 
        // maybe more fields here
        "viewpoints": [
            {
                "statement": "viewpoint detail",
                "support_percentage": approximate percentage
            }
        ]
    },
    "perspective_md": "the markdown of the perspective", // optional, based on the perspective
}
```

- utils:
    - [x] crawler.py to get llm friendly content from the url(with `trafilatura`)

## Exporter
- [ ] generate a proper markdown for human reading in the release page
- [ ] attach the json file to github release page


# PENDING
- [ ] generate a github pages site with the json file