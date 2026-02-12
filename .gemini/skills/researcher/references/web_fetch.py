import sys
import httpx
from bs4 import BeautifulSoup

def web_fetch(url: str):
    """Fetch and extract the main text content from a URL."""
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        if len(text) > 8000:
            text = text[:8000] + "\n\n[... content truncated at 8000 chars ...]"
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_fetch.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(web_fetch(url))
