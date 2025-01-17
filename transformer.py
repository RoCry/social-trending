from typing import Dict, Any

from litellm import acompletion


async def generate_perspective(
    title: str, content: str | None, comments: list[dict]
) -> Dict[str, Any]:
    """Generate AI perspective on the content and comments."""
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

    response = await acompletion(
        model="deepseek/deepseek-chat",  # Using deepseek as in comment_viewpoint.py
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


async def transform_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a story by adding AI-generated fields."""
    # Generate perspective if we have enough comments
    if len(story["comments"]) > 0:
        perspective = await generate_perspective(
            story["title"], story["content"], story["comments"]
        )
        story["_perspective"] = perspective
        story["_generated_at_comment_count"] = len(story["comments"])

    # Generate summary if we have content
    if story["content"]:
        summary_prompt = f"""Title: {story["title"]}
Content: {story["content"]}

Please provide a concise one-paragraph summary of the above content."""

        summary_response = await acompletion(
            model="deepseek-chat",
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


if __name__ == "__main__":
    import asyncio
    import json
    from pathlib import Path

    async def test():
        # Load the latest cache file
        cache_dir = Path("cache")
        cache_files = sorted(cache_dir.glob("*_hackernews.json"))
        if not cache_files:
            print("No cache files found")
            return

        latest_cache = cache_files[-1]
        with open(latest_cache) as f:
            stories = json.load(f)

        # Transform stories
        transformed = await transform_stories(stories)

        # Save transformed stories
        output_file = cache_dir / f"{latest_cache.stem}_transformed.json"
        with open(output_file, "w") as f:
            json.dump(transformed, f, indent=2)
        print(f"Transformed stories saved to {output_file}")

    asyncio.run(test())
