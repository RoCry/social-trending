from hackernews.util import normalize_html


def test_normalize_html_entities():
    test_cases = [
        ("I&#x27;m", "I'm"),
        ("&quot;Hello&quot;", '"Hello"'),
        ("Hello &amp; Goodbye", "Hello & Goodbye"),
        ("", ""),  # Empty string
        (None, None),  # None value
    ]

    for input_text, expected in test_cases:
        assert normalize_html(input_text) == expected


def test_normalize_html_content():
    html_content = """
    <p>Hello</p>
    <div>World &amp; Universe</div>
    """
    expected = "Hello World & Universe"
    assert normalize_html(html_content).replace("\n", " ").strip() == expected


def test_normalize_complex_content():
    html_content = """
    <p>I&#x27;m writing &quot;code&quot; with <code>Python</code></p>
    <pre>print(&quot;Hello&quot;)</pre>
    """
    result = normalize_html(html_content).strip()
    assert 'I\'m writing "code" with Python' in result
    assert 'print("Hello")' in result
    assert result.count("\n") == 1  # Verify there's one newline between elements
