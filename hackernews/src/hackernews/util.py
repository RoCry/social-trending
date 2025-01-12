import trafilatura

def normalize_html(html: str) -> str:
  if not html:
    return html

  result = trafilatura.extract(
    html,
    favor_precision=False,
    include_comments=False,
    deduplicate=True,
    output_format="txt",
  )

  # protect if not html
  return result if result else html
