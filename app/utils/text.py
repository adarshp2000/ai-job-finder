import html
from bs4 import BeautifulSoup

def html_to_text(s: str) -> str:
    """
    Converts HTML (or HTML-escaped HTML) into readable plain text.
    """
    if not s:
        return ""
    # Convert &lt; &gt; &amp; etc back to real characters
    s = html.unescape(s)
    # Strip tags
    soup = BeautifulSoup(s, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text