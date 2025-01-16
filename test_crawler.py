from crawler import url_to_markdown


def test_random_webpage():
    url = "https://www.latent.space/p/2025-papers"
    result = url_to_markdown(url)
    assert result is not None
    print(result)
