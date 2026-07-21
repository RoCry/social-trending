import json
import os
import re
from collections.abc import Awaitable, Callable
from typing import Protocol

from httpx import HTTPError
from loguru import logger
from models import Comment, Item, Perspective, Viewpoint
from smolllm import LLMResponse, StreamError, ask_llm

MIN_COMMENTS_FOR_PERSPECTIVE = 15
REFRESH_COMMENT_DELTA = 10
REFRESH_COMMENT_RATIO = 0.4

SYSTEM_PROMPT = """You are an expert social media analyst specializing in community discussion analysis.

Analyze the discussion by grouping similar reactions, identifying agreement and disagreement, and consolidating at most
five distinct viewpoints. Estimate the percentage of comments supporting each viewpoint and assess overall sentiment.

Return only these XML tags:
<title>concise title capturing the main discussion theme</title>
<summary>one paragraph capturing key discussion points and community reaction</summary>
<sentiment>positive, mixed, or negative</sentiment>
<viewpoint support="NN">one consolidated viewpoint</viewpoint>

Repeat <viewpoint> for each distinct viewpoint. The support attribute must be a number from 0 to 100.
"""


class PerspectiveGenerationError(RuntimeError):
    """The configured provider failed to produce a valid Perspective."""


class PerspectiveGenerator(Protocol):
    async def generate(self, title: str, comments: list[Comment]) -> Perspective: ...


def needs_refresh(item: Item) -> bool:
    current_count = len(item.comments)
    if item.generated_at_comment_count is None or current_count == 0:
        return False
    comment_delta = abs(item.generated_at_comment_count - current_count)
    return comment_delta > REFRESH_COMMENT_DELTA and comment_delta / current_count > REFRESH_COMMENT_RATIO


def _extract_xml(text: str, tag: str) -> str | None:
    if match := re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL):
        return match.group(1).strip()
    return None


def _parse_xml_perspective(text: str) -> Perspective | None:
    title = _extract_xml(text, "title")
    summary = _extract_xml(text, "summary")
    sentiment = _extract_xml(text, "sentiment")
    matches = re.findall(
        r"<viewpoint\s+support=[\"']([^\"']+)[\"']\s*>(.*?)</viewpoint>",
        text,
        re.DOTALL,
    )
    if not title or not summary or not sentiment or not matches:
        return None

    viewpoints = [
        Viewpoint(
            statement=statement.strip(),
            support_percentage=float(support.strip().removesuffix("%")),
        )
        for support, statement in matches
    ]
    return Perspective(
        title=title,
        summary=summary,
        sentiment=sentiment,
        viewpoints=viewpoints,
    )


def _parse_json_perspective(text: str) -> Perspective:
    stripped = text.strip()
    if match := re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL):
        stripped = match.group(1)
    return Perspective.model_validate(json.loads(stripped))


def parse_perspective(text: str) -> Perspective:
    try:
        if perspective := _parse_xml_perspective(text):
            return perspective
    except (TypeError, ValueError):
        pass

    try:
        return _parse_json_perspective(text)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError("Unable to parse Perspective response as XML or fenced JSON") from error


class SmolLLMPerspectiveGenerator:
    def __init__(
        self,
        *,
        model: str,
        ask: Callable[..., Awaitable[LLMResponse]] = ask_llm,
    ) -> None:
        self._model = model
        self._ask = ask

    @classmethod
    def from_env(cls) -> "SmolLLMPerspectiveGenerator":
        model = os.getenv("SMOLLLM_MODEL")
        if not model:
            raise ValueError("SMOLLLM_MODEL is required and must use provider/model form")

        provider, separator, model_name = model.partition("/")
        if not separator or not provider or not model_name:
            raise ValueError("SMOLLLM_MODEL must use provider/model form")

        api_key_name = f"{provider.upper()}_API_KEY"
        if not os.getenv(api_key_name):
            raise ValueError(f"{api_key_name} is required for {model}")
        return cls(model=model)

    async def generate(self, title: str, comments: list[Comment]) -> Perspective:
        comments_text = "\n".join(f"- {comment.author}: {comment.content[:500]}" for comment in comments)
        prompt = f"Title: {title}\nComments:\n{comments_text}"
        logger.info("Generating Perspective for {!r}", title)
        try:
            response = await self._ask(
                prompt,
                system_prompt=SYSTEM_PROMPT,
                model=self._model,
                stream=False,
            )
        except (HTTPError, StreamError, TimeoutError, TypeError, ValueError) as error:
            raise PerspectiveGenerationError(f"Failed to generate Perspective for {title!r}") from error

        try:
            return parse_perspective(response.text)
        except ValueError as error:
            raise PerspectiveGenerationError(f"Failed to generate Perspective for {title!r}") from error
