from __future__ import annotations

from bs4 import BeautifulSoup


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.title
    if not tag:
        return ""
    text = tag.string or tag.get_text()
    return text.strip()
