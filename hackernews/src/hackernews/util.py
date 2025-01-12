import html
import re
import trafilatura

def normalize_html(html_text: str) -> str:
    if not html_text:
        return html_text

    # First unescape HTML entities
    text = html.unescape(html_text)
    
    # Simple HTML tag removal if trafilatura fails
    if "<" in text and ">" in text:
        # Try trafilatura first
        result = trafilatura.extract(
            text,
            favor_precision=False,
            include_comments=False,
            deduplicate=True,
            output_format="txt",
        )
        
        # Fallback to simple HTML cleaning if trafilatura returns None
        if not result:
            # Replace specific tags with newlines
            text = re.sub(r'</(?:p|div|pre|br)>', '\n', text)
            # Remove remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            # Normalize whitespace but preserve intentional newlines
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s+', '\n', text)
            text = re.sub(r'\n+', '\n', text)
            return text.strip()
            
        return result

    return text
