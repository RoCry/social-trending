from typing import Dict, Any
import litellm
from utils import logger
import json

async def generate_perspective(
    title: str, content: str | None, comments: list[dict]
) -> Dict[str, Any]:
    """Generate AI perspective on the content and comments."""
    logger.info(f"Generating perspective for {title}")
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


async def transform_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a story by adding AI-generated fields."""
    # Skip if we already have AI fields and they don't need regeneration
    if all(
        k in story for k in ["_summary", "_perspective", "_generated_at_comment_count"]
    ):
        return story

    # Generate perspective if we have enough comments
    if len(story["comments"]) > 0 and story.get("_perspective") is None:
        perspective = await generate_perspective(
            story["title"], story["content"], story["comments"]
        )
        story["_perspective"] = json.loads(perspective)
        story["_generated_at_comment_count"] = len(story["comments"])

    # Generate summary if we have content
    if story["content"] and story.get("_summary") is None:
        logger.info(f"Generating summary for {story['title']}")
        summary_prompt = f"""Title: {story["title"]}
Content: {story["content"]}

Please provide a concise one-paragraph summary of the above content."""

        summary_response = await litellm.acompletion(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": summary_prompt}],
        )
        story["_summary"] = summary_response.choices[0].message.content

    return story


async def transform_stories(stories: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Transform multiple stories in parallel."""
    transformed = []
    for story in stories:
        transformed_story = await transform_story(story)
        transformed.append(transformed_story)
    return transformed
