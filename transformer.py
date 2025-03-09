from typing import List
from litellm import Router
from utils import logger
import json
import os
from models import Item, Perspective, Comment
from datetime import datetime
from db import Database
from typing import Optional


async def _generate_perspective(
    title: str, comments: list[Comment], router: Router
) -> Perspective:
    """Generate AI perspective based on the title and community discussion."""
    logger.info(f"Generating perspective for '{title}'")
    # Truncate comments to 500 characters to stay within token limits
    comments_text = "\n".join([f"- {c.author}: {c.content[:500]}" for c in comments])

    prompt = f"""
Title: {title}
Comments:
{comments_text}
"""

    # The system prompt is designed to:
    # 1. Focus on discussion analysis rather than content interpretation
    # 2. Identify patterns and consensus in community reactions
    # 3. Extract meaningful insights from diverse viewpoints
    # 4. Quantify the level of agreement/disagreement
    system_prompt = """You are an expert social media analyst specializing in community discussion analysis.

Analyze the discussion following these steps:

1. Comment Analysis:
   - Group similar opinions and reactions
   - Note recurring themes and patterns
   - Identify key points of agreement/disagreement

2. Viewpoint Consolidation:
   - Merge similar viewpoints (>70% overlap)
   - Keep only distinct, well-supported perspectives
   - Limit to maximum 5 viewpoints
   - Calculate approximate support percentage

3. Community Sentiment:
   - Evaluate overall tone and engagement
   - Consider consensus vs controversy
   - Note strength of dominant opinions

Output in this exact format:
{
    "title": "concise title capturing main discussion theme",
    "summary": "one paragraph capturing key discussion points and community reaction",
    "sentiment": "overall sentiment (positive/mixed/negative)",
    "viewpoints": [
        {
            "statement": "viewpoint detail",
            "support_percentage": approximate percentage
        }
    ]
}"""

    response = await router.acompletion(
        model=os.getenv("LITELLM_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    json_str = response.choices[0].message.content
    if json_str.startswith("```json") and json_str.endswith("```"):
        json_str = json_str[7:-3]
    json_str = json_str.strip()
    logger.info(f"Generated perspective: {json_str}")
    perspective_data = json.loads(json_str)
    return Perspective(**perspective_data)


async def _transform_item_if_needed(item: Item, router: Router) -> Item:
    if item.generated_at_comment_count is not None:
        comment_diff = abs(item.generated_at_comment_count - len(item.comments))
        # Skip if comments haven't changed significantly (less than 5 or 10%)
        if comment_diff <= 5 or comment_diff / len(item.comments) <= 0.1:
            logger.info(
                f"Skipping perspective generation for '{item.title}' with comment count {len(item.comments)} (last generated at {item.generated_at_comment_count})"
            )
            return item

        logger.info(
            f"Comments changed from {item.generated_at_comment_count} to {len(item.comments)}, regenerating perspective for '{item.title}'"
        )
        item.ai_perspective = None

    # Generate perspective if we have enough comments
    MIN_COMMENTS_FOR_PERSPECTIVE = 5
    if (
        len(item.comments) >= MIN_COMMENTS_FOR_PERSPECTIVE
        and item.ai_perspective is None
    ):
        try:
            perspective = await _generate_perspective(
                item.title, item.comments, router=router
            )
            item.ai_perspective = perspective
            item.generated_at_comment_count = len(item.comments)
        except Exception as e:
            logger.error(f"Failed to generate perspective for '{item.title}': {str(e)}")
    elif len(item.comments) > 0 and len(item.comments) < MIN_COMMENTS_FOR_PERSPECTIVE:
        logger.info(
            f"Skipping perspective generation for '{item.title}' due to insufficient comments ({len(item.comments)})"
        )

    return item


def perspective_to_md(perspective: Perspective, comments: List[Comment]) -> str:
    sections = []

    # Title section
    sections.append(f"### AI Perspective: {perspective.title}\n")

    # Summary and sentiment section
    sections.append("<details><summary>Perspective Summary</summary>")
    sections.append(f"{perspective.summary}")
    sections.append("</details>\n")

    # Viewpoints section
    if perspective.viewpoints:
        sections.append(
            f"### {len(perspective.viewpoints)} Key Viewpoints ({len(comments)} comments)"
        )
        sections.append(f"> **Overall Sentiment**: {perspective.sentiment}\n")
        for vp in perspective.viewpoints:
            sections.append(f"- {vp.statement} _(~{vp.support_percentage:.0f}%)_")

    return "\n".join(sections)


def items_to_md(now: datetime, items: List[Item]) -> str:
    sections = []

    for item in items:
        sections.append(f"## [{item.title}]({item.url})\n\n")

        if item.ai_perspective:
            sections.append(perspective_to_md(item.ai_perspective, item.comments))

        sections.append("---\n")

    return "\n".join(sections)


# skip_none_perspective: if true, skip items with no perspective
def items_to_json_feed(
    now: datetime, items: List[Item], skip_none_perspective: bool = False
) -> dict:
    def _generate_content_text(item: Item) -> Optional[str]:
        sections = []

        # AI Perspective section
        if item.ai_perspective:
            sections.append("AI Perspective:")
            sections.append(f"Title: {item.ai_perspective.title}")
            sections.append(f"Summary: {item.ai_perspective.summary}")
            sections.append(f"Sentiment: {item.ai_perspective.sentiment}")
            if item.ai_perspective.viewpoints:
                sections.append("Viewpoints:")
                for vp in item.ai_perspective.viewpoints:
                    sections.append(f"- {vp.statement} ({vp.support_percentage}%)")

        # Original content section
        if item.content:
            sections.append("\nOriginal Content:")
            sections.append(item.content)

        # Comments section
        if item.comments:
            sections.append("\nComments:")
            for comment in item.comments:
                sections.append(f"{comment.author}: {comment.content}")

        return "\n".join(sections) if sections else None

    def _generate_content_html(item: Item) -> Optional[str]:
        html_parts = []

        # Source URL section
        if item.original_url and item.original_url != item.url:
            html_parts.append(
                f'<p><strong>Source:</strong> <a href="{item.original_url}">{item.original_url}</a></p>'
            )

        # AI Perspective section
        if item.ai_perspective:
            html_parts.append("<h2>AI Perspective</h2>")
            html_parts.append(f"<h3>{item.ai_perspective.title}</h3>")
            html_parts.append(
                f"<p><strong>Summary:</strong> {item.ai_perspective.summary}</p>"
            )
            html_parts.append(
                f"<p><strong>Overall Sentiment:</strong> {item.ai_perspective.sentiment}</p>"
            )

            if item.ai_perspective.viewpoints:
                html_parts.append("<h4>Key Viewpoints</h4>")
                html_parts.append("<ul>")
                for vp in item.ai_perspective.viewpoints:
                    html_parts.append(
                        f"<li>{vp.statement} <em>({vp.support_percentage:.0f}%)</em></li>"
                    )
                html_parts.append("</ul>")

        # Original content section
        if item.content_html:
            html_parts.append(item.content_html)
        elif item.content:
            html_parts.append(f"<p>{item.content}</p>")

        # Comments section
        if item.comments:
            html_parts.append("<h4>Comments</h4>")
            html_parts.append("<ul>")
            for comment in item.comments:
                html_parts.append(
                    f"<li><em>{comment.author}</em>: {comment.content}</li>"
                )
            html_parts.append("</ul>")

        return "\n".join(html_parts) if html_parts else None

    def _item_to_json_item(item: Item) -> Optional[dict]:
        if skip_none_perspective and not item.ai_perspective:
            return None
        text = _generate_content_text(item)
        html = _generate_content_html(item)
        if not text and not html:
            return None
        summary = item.ai_perspective.title if item.ai_perspective else item.title
        return {
            "id": item.id,
            "url": item.url,
            "title": f"{item.title} ({len(item.comments)})",
            "content_text": text,
            "content_html": html,
            "summary": summary,
            "date_published": (
                item.published_at.isoformat()
                if item.published_at
                else item.created_at.isoformat()
            ),
            "date_modified": item.updated_at.isoformat(),
            "authors": (
                [{"name": comment.author} for comment in item.comments[:1]]
                if item.comments
                else None
            ),
            "tags": ["hackernews"],
        }

    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Social Trending - Hacker News",
        "home_page_url": "https://news.ycombinator.com/",
        "feed_url": "https://github.com/RoCry/social-trending/releases/download/latest/hackernews.rss.json",
        "description": "Top stories from Hacker News with AI-powered analysis",
        "authors": [
            {
                "name": "Social Trending Bot",
                "url": "https://github.com/RoCry/social-trending",
            }
        ],
        "language": "en-US",
        "items": [],
    }
    for item in items:
        json_item = _item_to_json_item(item)
        if json_item:
            feed["items"].append(json_item)
    return feed


async def transform_items(items: List[Item], db: Database, router=None) -> List[Item]:
    """Transform multiple items in parallel and optionally save to database progressively."""
    transformed = []
    for item in items:
        try:
            transformed_item = await _transform_item_if_needed(item, router=router)
            await db.upsert_item(transformed_item)
            logger.info(
                f"Saved transformed item '{transformed_item.title}' to database"
            )
            transformed.append(transformed_item)
        except Exception as e:
            logger.error(f"Failed to transform item '{item.title}': {str(e)}")
            transformed.append(item)  # Keep the original item on failure
    return transformed
