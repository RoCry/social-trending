import asyncio
from datetime import UTC, datetime

import pytest
from main import apply_perspectives, llm_enabled
from models import Comment, Item


@pytest.mark.parametrize("value", [None, "", "false", "FALSE"])
def test_llm_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv("ENABLE_LLM", raising=False)
    else:
        monkeypatch.setenv("ENABLE_LLM", value)

    assert llm_enabled() is False


def test_llm_requires_explicit_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_LLM", "true")

    assert llm_enabled() is True


def test_invalid_llm_flag_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_LLM", "sometimes")

    with pytest.raises(ValueError, match="ENABLE_LLM must be 'true' or 'false'"):
        llm_enabled()


def test_disabled_llm_leaves_items_untransformed_without_model_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SMOLLLM_MODEL", raising=False)
    now = datetime(2026, 7, 20, tzinfo=UTC)
    item = Item(
        id="1",
        title="No paid analysis",
        url="https://example.test/1",
        comments=[Comment(author="reader", content="comment")] * 15,
        created_at=now,
        updated_at=now,
    )
    items = [item]

    result = asyncio.run(apply_perspectives(items=items, enabled=False))

    assert result is items
    assert item.ai_perspective is None
