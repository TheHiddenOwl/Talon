from bs4 import BeautifulSoup
from typing import Dict, List, Optional

class HtmlParser:
    @staticmethod
    def extract_links(html: str, base_url: Optional[str] = None) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            links.append(a["href"])
        return links

    @staticmethod
    def extract_metadata(html: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, "lxml")
        metadata = {}
        if soup.title:
            metadata["title"] = soup.title.string

        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content
        return metadata
