from typing import Dict, Any
import litellm
from utils import logger
import json


async def _generate_perspective(
    title: str, content: str | None, comments: list[dict]
) -> Dict[str, Any]:
    """Generate AI perspective on the content and comments."""
    logger.info(f"Generating perspective for '{title}'")
    comments_text = "\n".join([f"- {c['author']}: {c['content']}" for c in comments])

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
        model="deepseek/deepseek-chat",  # Using deepseek as in comment_viewpoint.py
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content

async def _transform_item_if_needed(item: Dict[str, Any]) -> Dict[str, Any]:
    if all(
        k in item for k in ["_summary", "_perspective", "_generated_at_comment_count"]
    ):
        # already generated, check if comments changed a lot
        new_comments_count = item["_generated_at_comment_count"] - len(item["comments"])
        if new_comments_count <= 2:
            logger.info(f"Skipping ai generation for '{item['title']}' with comment count {len(item['comments'])}")
            return item

        logger.info(f"Comments changed from {item['_generated_at_comment_count']} to {len(item['comments'])}, regenerating perspective for '{item['title']}'")
        item["_perspective"] = None

    # Generate perspective if we have enough comments
    if len(item["comments"]) > 0 and item.get("_perspective") is None:
        perspective = await _generate_perspective(
            item["title"], item["content"], item["comments"]
        )
        item["_perspective"] = json.loads(perspective)
        item["_generated_at_comment_count"] = len(item["comments"])

    # Generate summary if we have content
    if item["content"] and item.get("_summary") is None:
        logger.info(f"Generating summary for '{item['title']}'")
        summary_prompt = f"""Title: {item["title"]}
Content: {item["content"]}

Please provide a concise one-paragraph summary of the above content."""

        summary_response = await litellm.acompletion(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": summary_prompt}],
        )
        item["_summary"] = summary_response.choices[0].message.content

    return item


async def transform_items(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Transform multiple items in parallel."""
    transformed = []
    for item in items:
        transformed_item = await _transform_item_if_needed(item)
        transformed.append(transformed_item)
    return transformed
