import asyncio
from datetime import UTC, datetime

import pytest
from models import Comment, Item
from perspective_generator import (
    PerspectiveGenerationError,
    SmolLLMPerspectiveGenerator,
    needs_refresh,
    parse_perspective,
)
from smolllm import LLMResponse


def test_parse_perspective_reads_xml_tags_and_repeated_viewpoints() -> None:
    response = """
Some harmless leading text.
<title>Why readers agree</title>
<summary>Most readers support the change.</summary>
<sentiment>positive</sentiment>
<viewpoint support="72">It removes repeated work.</viewpoint>
<viewpoint support="28.5">Migration still needs care.</viewpoint>
"""

    perspective = parse_perspective(response)

    assert perspective.model_dump() == {
        "title": "Why readers agree",
        "summary": "Most readers support the change.",
        "sentiment": "positive",
        "viewpoints": [
            {
                "statement": "It removes repeated work.",
                "support_percentage": 72.0,
            },
            {
                "statement": "Migration still needs care.",
                "support_percentage": 28.5,
            },
        ],
    }


def test_parse_perspective_falls_back_to_fenced_json() -> None:
    perspective = parse_perspective(
        """```json
{
  "title": "Fallback",
  "summary": "JSON worked.",
  "sentiment": "mixed",
  "viewpoints": [{"statement": "One view", "support_percentage": 55}]
}
```"""
    )

    assert perspective.title == "Fallback"
    assert perspective.viewpoints[0].support_percentage == 55


def test_parse_perspective_rejects_garbage_cleanly() -> None:
    with pytest.raises(ValueError, match="Unable to parse Perspective response as XML or fenced JSON"):
        parse_perspective("not structured output")


@pytest.mark.parametrize(
    ("generated_count", "current_count", "expected"),
    [
        (None, 15, False),
        (15, 25, False),  # Difference is exactly 10.
        (20, 30, False),  # Ratio is below 40%.
        (18, 30, False),  # Ratio is exactly 40%.
        (15, 26, True),  # Both boundaries are exceeded.
        (15, 0, False),  # No discussion remains to refresh from.
    ],
)
def test_needs_refresh_pins_comment_change_thresholds(
    generated_count: int | None, current_count: int, expected: bool
) -> None:
    now = datetime(2026, 7, 17, tzinfo=UTC)
    item = Item(
        id="1",
        title="Thresholds",
        url="https://example.test/1",
        comments=[{"author": "reader", "content": "comment"}] * current_count,
        created_at=now,
        updated_at=now,
        generated_at_comment_count=generated_count,
    )

    assert needs_refresh(item) is expected


def test_generator_reads_typed_smolllm_response() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    async def fake_ask(prompt: str, **kwargs: object) -> LLMResponse:
        calls.append((prompt, kwargs))
        return LLMResponse(
            text=(
                "<title>Typed response</title>"
                "<summary>The seam parsed LLMResponse.text.</summary>"
                "<sentiment>positive</sentiment>"
                '<viewpoint support="100">One public path.</viewpoint>'
            ),
            model="smolserver/fast",
            model_name="fast",
        )

    generator = SmolLLMPerspectiveGenerator(model="smolserver/fast", ask=fake_ask)
    perspective = asyncio.run(
        generator.generate(title="A title", comments=[Comment(author="reader", content="A useful comment")])
    )

    assert perspective.title == "Typed response"
    assert calls[0][0] == "Title: A title\nComments:\n- reader: A useful comment"
    assert calls[0][1]["model"] == "smolserver/fast"
    assert calls[0][1]["stream"] is False


def test_generator_maps_provider_failure_to_generation_error() -> None:
    async def failed_ask(prompt: str, **kwargs: object) -> LLMResponse:
        raise ValueError("provider returned invalid data")

    generator = SmolLLMPerspectiveGenerator(model="smolserver/summary", ask=failed_ask)

    with pytest.raises(PerspectiveGenerationError, match="Failed to generate Perspective") as error:
        asyncio.run(
            generator.generate(title="A title", comments=[Comment(author="reader", content="A useful comment")])
        )

    assert isinstance(error.value.__cause__, ValueError)


def test_generator_fails_fast_on_unexpected_error() -> None:
    async def broken_ask(prompt: str, **kwargs: object) -> LLMResponse:
        raise AssertionError("unexpected implementation defect")

    generator = SmolLLMPerspectiveGenerator(model="smolserver/summary", ask=broken_ask)

    with pytest.raises(AssertionError, match="unexpected implementation defect"):
        asyncio.run(
            generator.generate(title="A title", comments=[Comment(author="reader", content="A useful comment")])
        )


def test_generator_configuration_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMOLLLM_MODEL", raising=False)
    with pytest.raises(ValueError, match="SMOLLLM_MODEL is required"):
        SmolLLMPerspectiveGenerator.from_env()

    monkeypatch.setenv("SMOLLLM_MODEL", "gemini/gemini-2.0-flash")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        SmolLLMPerspectiveGenerator.from_env()
