from dataclasses import dataclass

from models import Comment, Item, Perspective


@dataclass(frozen=True, slots=True)
class FeedIdentity:
    source_name: str
    feed_title: str
    home_page_url: str
    feed_url: str
    tags: tuple[str, ...]


def _perspective_to_markdown(perspective: Perspective, comments: list[Comment]) -> str:
    sections = [
        f"### AI Perspective: {perspective.title}\n",
        "<details><summary>Perspective Summary</summary>",
        perspective.summary,
        "</details>\n",
    ]
    if perspective.viewpoints:
        sections.extend(
            [
                f"### {len(perspective.viewpoints)} Key Viewpoints ({len(comments)} comments)",
                f"> **Overall Sentiment**: {perspective.sentiment}\n",
            ]
        )
        sections.extend(
            f"- {viewpoint.statement} _(~{viewpoint.support_percentage:.0f}%)_" for viewpoint in perspective.viewpoints
        )
    return "\n".join(sections)


def items_to_markdown(items: list[Item]) -> str:
    sections: list[str] = []
    for item in items:
        sections.append(f"## [{item.title}]({item.url})\n\n")
        if item.ai_perspective:
            sections.append(_perspective_to_markdown(item.ai_perspective, item.comments))
        sections.append("---\n")
    return "\n".join(sections)


def items_to_raw_json(items: list[Item]) -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in items]


def _content_text(item: Item) -> str | None:
    sections: list[str] = []

    if perspective := item.ai_perspective:
        sections.extend(
            [
                "AI Perspective:",
                f"Title: {perspective.title}",
                f"Summary: {perspective.summary}",
                f"Sentiment: {perspective.sentiment}",
            ]
        )
        if perspective.viewpoints:
            sections.append("Viewpoints:")
            sections.extend(
                f"- {viewpoint.statement} ({viewpoint.support_percentage}%)" for viewpoint in perspective.viewpoints
            )

    if item.content:
        sections.extend(["\nOriginal Content:", item.content])

    if item.comments:
        sections.append("\nComments:")
        sections.extend(f"{comment.author}: {comment.content}" for comment in item.comments)

    return "\n".join(sections) if sections else None


def _content_html(item: Item) -> str | None:
    parts: list[str] = []

    if item.original_url and item.original_url != item.url:
        parts.append(f'<p><strong>Source:</strong> <a href="{item.original_url}">{item.original_url}</a></p>')

    if perspective := item.ai_perspective:
        parts.extend(
            [
                "<h2>AI Perspective</h2>",
                f"<h3>{perspective.title}</h3>",
                f"<p><strong>Summary:</strong> {perspective.summary}</p>",
                f"<p><strong>Overall Sentiment:</strong> {perspective.sentiment}</p>",
            ]
        )
        if perspective.viewpoints:
            parts.extend(["<h4>Key Viewpoints</h4>", "<ul>"])
            parts.extend(
                f"<li>{viewpoint.statement} <em>({viewpoint.support_percentage:.0f}%)</em></li>"
                for viewpoint in perspective.viewpoints
            )
            parts.append("</ul>")

    if item.content_html:
        parts.append(item.content_html)
    elif item.content:
        parts.append(f"<p>{item.content}</p>")

    if item.comments:
        parts.extend(["<h4>Comments</h4>", "<ul>"])
        parts.extend(f"<li><em>{comment.author}</em>: {comment.content}</li>" for comment in item.comments)
        parts.append("</ul>")

    return "\n".join(parts) if parts else None


def _json_feed_item(item: Item, *, tags: tuple[str, ...]) -> dict[str, object] | None:
    content_text = _content_text(item)
    content_html = _content_html(item)
    if not content_text and not content_html:
        return None

    return {
        "id": item.id,
        "url": item.url,
        "title": f"{item.title} ({len(item.comments)})",
        "content_text": content_text,
        "content_html": content_html,
        "summary": item.ai_perspective.title if item.ai_perspective else item.title,
        "date_published": (item.published_at or item.created_at).isoformat(),
        "date_modified": item.updated_at.isoformat(),
        "authors": ([{"name": item.comments[0].author}] if item.comments else None),
        "tags": list(tags),
    }


def items_to_json_feed(
    items: list[Item],
    *,
    identity: FeedIdentity,
    skip_none_perspective: bool = False,
) -> dict[str, object]:
    feed_items = [
        rendered
        for item in items
        if not skip_none_perspective or item.ai_perspective
        if (rendered := _json_feed_item(item, tags=identity.tags)) is not None
    ]
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": identity.feed_title,
        "home_page_url": identity.home_page_url,
        "feed_url": identity.feed_url,
        "description": f"Top stories from {identity.source_name} with AI-powered analysis",
        "authors": [
            {
                "name": "Social Trending Bot",
                "url": "https://github.com/RoCry/social-trending",
            }
        ],
        "language": "en-US",
        "items": feed_items,
    }
