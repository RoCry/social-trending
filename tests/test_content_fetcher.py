import asyncio
import threading
from collections.abc import Callable

import pytest
import requests
from content_fetcher import ContentFetcher

FetchResult = tuple[str | None, str | None]


@pytest.mark.parametrize(
    ("successful_tier", "expected_calls", "expected"),
    [
        ("trafilatura", ["trafilatura"], ("text-1", "<p>html-1</p>")),
        (
            "beautifulsoup",
            ["trafilatura", "beautifulsoup"],
            ("text-2", "<p>html-2</p>"),
        ),
        (
            "jina",
            ["trafilatura", "beautifulsoup", "jina"],
            ("text-3", None),
        ),
        (None, ["trafilatura", "beautifulsoup", "jina"], (None, None)),
    ],
)
def test_fallback_chain_stops_at_the_first_successful_tier(
    successful_tier: str | None,
    expected_calls: list[str],
    expected: FetchResult,
) -> None:
    calls: list[str] = []

    def extractor(name: str, result: FetchResult) -> Callable[[str], FetchResult]:
        def fetch(url: str) -> FetchResult:
            assert url == "https://example.test/article"
            calls.append(name)
            if successful_tier == name:
                return result
            if name == "beautifulsoup":
                raise requests.RequestException("request failure falls through")
            return None, None

        return fetch

    fetcher = ContentFetcher(
        extractors=(
            ("trafilatura", extractor("trafilatura", ("text-1", "<p>html-1</p>"))),
            ("beautifulsoup", extractor("beautifulsoup", ("text-2", "<p>html-2</p>"))),
            ("jina", extractor("jina", ("text-3", None))),
        )
    )

    assert asyncio.run(fetcher.fetch("https://example.test/article")) == expected
    assert calls == expected_calls


def test_unexpected_extractor_error_fails_fast() -> None:
    def broken_extractor(url: str) -> FetchResult:
        raise RuntimeError(f"programming error while fetching {url}")

    fetcher = ContentFetcher(extractors=(("broken", broken_extractor),))

    with pytest.raises(RuntimeError, match="programming error"):
        asyncio.run(fetcher.fetch("https://example.test/article"))


def test_fetch_runs_the_synchronous_chain_off_the_event_loop() -> None:
    event_loop_thread = threading.get_ident()

    def record_thread(url: str) -> FetchResult:
        return str(threading.get_ident()), None

    fetcher = ContentFetcher(extractors=(("thread-probe", record_thread),))

    worker_thread, _ = asyncio.run(fetcher.fetch("https://example.test/article"))

    assert worker_thread is not None
    assert int(worker_thread) != event_loop_thread
