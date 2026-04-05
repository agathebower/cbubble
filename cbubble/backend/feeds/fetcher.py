"""RSS/Atom feed fetcher with HTML fallback."""

import httpx
import feedparser
import logging
from bs4 import BeautifulSoup
from dataclasses import dataclass

log = logging.getLogger("cbubble.feeds")
HEADERS = {"User-Agent": "cBubble/1.0 (Personal News Aggregator)"}


@dataclass
class FeedItem:
    title: str
    url: str
    source_name: str
    category: str
    image_url: str | None = None
    published_at: str | None = None
    content_snippet: str | None = None


async def fetch_rss(source_name, rss_url, category) -> list[FeedItem]:
    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:25]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            image = None
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                enc = entry.enclosures[0]
                if enc.get("type", "").startswith("image"):
                    image = enc.get("href")
            content = ""
            if hasattr(entry, "summary"):
                content = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]
            elif hasattr(entry, "content") and entry.content:
                content = BeautifulSoup(entry.content[0].value, "html.parser").get_text()[:500]
            published = entry.get("published", entry.get("updated"))
            items.append(FeedItem(title=title, url=link, source_name=source_name,
                                  category=category, image_url=image,
                                  published_at=published,
                                  content_snippet=content if content else None))
        log.info("Fetched %d items from %s", len(items), source_name)
    except Exception as e:
        log.error("Failed to fetch RSS from %s: %s", source_name, e)
    return items


async def fetch_article_content(url) -> tuple[str | None, str | None]:
    """Fetch article text and og:image URL from the page.

    Returns (content, og_image_url).
    """
    try:
        async with httpx.AsyncClient(timeout=20.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract Open Graph / Twitter image before stripping tags
        og_image = None
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "") or meta.get("name", "")
            if prop == "og:image" and meta.get("content"):
                og_image = meta["content"].strip()
                break
        if not og_image:
            for meta in soup.find_all("meta"):
                prop = meta.get("property", "") or meta.get("name", "")
                if prop in ("twitter:image", "twitter:image:src") and meta.get("content"):
                    og_image = meta["content"].strip()
                    break

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.find("div", class_="post-content")
        text = (article or soup).get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        content = "\n".join(lines)[:8000]
        return (content if len(content) > 100 else None, og_image)
    except Exception as e:
        log.error("Failed to fetch article from %s: %s", url, e)
        return (None, None)
