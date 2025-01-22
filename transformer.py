from typing import List
import litellm
from utils import logger
import json
from models import Item, Perspective, Comment
from datetime import datetime


async def _generate_perspective(
    title: str, content: str | None, comments: list[dict]
) -> Perspective:
    """Generate AI perspective on the content and comments."""
    logger.info(f"Generating perspective for '{title}'")
    comments_text = "\n".join([f"- {c.author}: {c.content}" for c in comments])

    prompt = f"""
Title: {title}
Content: {content or "[No content available]"}
Comments:
{comments_text}
"""

    system_prompt = """You are an expert social media analyst with deep understanding of community discussions.

First, read through the content and comments step by step:

1. Content analysis:
   - Extract main topic and key points
   - Identify the core argument or information

2. Comment analysis:
   - Examine each comment carefully
   - Group similar viewpoints together
   - Note the sentiment and strength of each opinion

3. Consolidation:
   - Merge highly similar viewpoints (>70% overlap)
   - Keep only the most representative viewpoint from each group
   - Limit to maximum 5 distinct viewpoints
   - Calculate approximate support percentage for each

4. Final synthesis:
   - Determine overall community sentiment
   - Find the key areas of agreement/disagreement
   - Identify most impactful perspectives

Output the final result in this exact format:
{
    "title": "concise but descriptive title",
    "summary": "comprehensive summary in one paragraph",
    "sentiment": "overall sentiment (positive/mixed/negative)",
    "viewpoints": [
        {
            "statement": "viewpoint detail",
            "support_percentage": approximate percentage
        }
    ]
}"""

    response = await litellm.acompletion(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    perspective_data = json.loads(response.choices[0].message.content)
    return Perspective(**perspective_data)


async def _transform_item_if_needed(item: Item) -> Item:
    if all(
        k in item.model_fields_set
        for k in ["ai_summary", "ai_perspective", "generated_at_comment_count"]
    ):
        # already generated, check if comments changed a lot
        if item.generated_at_comment_count is not None:
            comment_diff = abs(item.generated_at_comment_count - len(item.comments))
            if comment_diff <= 5:
                logger.info(
                    f"Skipping ai generation for '{item.title}' with comment count {len(item.comments)} (last generated at {item.generated_at_comment_count})"
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
        perspective = await _generate_perspective(
            item.title, item.content, item.comments
        )
        item.ai_perspective = perspective
        item.generated_at_comment_count = len(item.comments)
    elif len(item.comments) > 0 and len(item.comments) < MIN_COMMENTS_FOR_PERSPECTIVE:
        logger.info(
            f"Skipping perspective generation for '{item.title}' due to insufficient comments ({len(item.comments)})"
        )

    # Generate summary if we have content
    if item.content and item.ai_summary is None:
        logger.info(f"Generating summary for '{item.title}'")
        summary_prompt = f"""Title: {item.title}
Content: {item.content}

Please provide a concise one-paragraph summary of the above content."""

        summary_response = await litellm.acompletion(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": summary_prompt}],
        )
        item.ai_summary = summary_response.choices[0].message.content

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

        if item.ai_summary:
            sections.append("<details><summary>AI Summary</summary>")
            sections.append(f"{item.ai_summary}\n</details>\n\n")

        if item.ai_perspective:
            sections.append(perspective_to_md(item.ai_perspective, item.comments))

        sections.append("---\n")

    return "\n".join(sections)


async def transform_items(items: List[Item]) -> List[Item]:
    """Transform multiple items in parallel."""
    transformed = []
    for item in items:
        transformed_item = await _transform_item_if_needed(item)
        transformed.append(transformed_item)
    return transformed
