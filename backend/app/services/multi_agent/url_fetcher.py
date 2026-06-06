import httpx
import logging
import re
from typing import Dict, Any
from html.parser import HTMLParser

log = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignore_tags = {"script", "style", "nav", "footer", "header", "aside", "head"}
        self.current_tags = []
        self.text_parts = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        self.current_tags.append(tag.lower())
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if self.current_tags:
            self.current_tags.pop()
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):

        if any(ignored in self.current_tags for ignored in self.ignore_tags):
            return
        if self.in_title:
            self.title = (self.title + data).strip()
        else:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_text(self) -> str:
        return " ".join(self.text_parts)

class URLFetcher:
    @staticmethod
    async def fetch(url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/91.0.4472.124 Safari/537.36"
                    )
                }
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"HTTP status code {response.status_code}")
                
                html_content = response.text
                parser = HTMLTextExtractor()
                parser.feed(html_content)
                
                title = parser.title or "Untitled Page"
                extracted_content = parser.get_text()
                

                extracted_content = re.sub(r'\s+', ' ', extracted_content).strip()
                
                return {
                    "url": url,
                    "title": title,
                    "extracted_content": extracted_content
                }
        except Exception as e:
            log.warning("Failed to fetch web content from %s: %s", url, e)
            return {
                "url": url,
                "title": "Failed to load",
                "extracted_content": f"[Could not retrieve web content from {url}. Error: {str(e)}]"
            }
