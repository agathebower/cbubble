"""RSS/Atom feed fetcher with HTML fallback."""

import socket
import logging
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

import httpx
import feedparser
import bleach
from bs4 import BeautifulSoup
from dataclasses import dataclass

log = logging.getLogger("cbubble.feeds")
HEADERS = {"User-Agent": "cBubble/1.0 (Personal News Aggregator)"}

# Private / loopback / link-local ranges that must never be fetched
_PRIVATE_NETS = [
    ip_network(r) for r in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",   # link-local / AWS metadata
        "::1/128",
        "fc00::/7",
    )
]
_ALLOWED_SCHEMES = {"http", "https"}


def _validate_url(url: str) -> str:
    """Validate URL scheme and resolve hostname to block SSRF.

    Returns the url unchanged if safe; raises ValueError otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")
    try:
        addr = ip_address(socket.gethostbyname(hostname))
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolution failed for {hostname!r}: {exc}") from exc
    if any(addr in net for net in _PRIVATE_NETS):
        raise ValueError(f"Blocked: {addr} resolves to a private/reserved range")
    return url


def _sanitize_text(raw: str, max_len: int = 500) -> str:
    """Strip all HTML tags and truncate."""
    return bleach.clean(raw, tags=[], strip=True)[:max_len]


def _safe_img(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    try:
        _validate_url(url)
        return url
    except ValueError:
        return None


def _extract_rss_image(entry) -> str | None:
    """Try every common RSS image location in priority order."""
    # 1. media:content
    if hasattr(entry, "media_content") and entry.media_content:
        img = _safe_img(entry.media_content[0].get("url"))
        if img:
            return img
    # 2. media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        img = _safe_img(entry.media_thumbnail[0].get("url"))
        if img:
            return img
    # 3. enclosure (podcast-style)
    if hasattr(entry, "enclosures") and entry.enclosures:
        enc = entry.enclosures[0]
        if enc.get("type", "").startswith("image"):
            img = _safe_img(enc.get("href"))
            if img:
                return img
    # 4. first <img> in summary/content HTML
    for field in ("summary", "content"):
        html = getattr(entry, field, None)
        if isinstance(html, list):
            html = html[0].value if html else None
        if html:
            soup = BeautifulSoup(html, "html.parser")
            tag = soup.find("img")
            if tag:
                img = _safe_img(tag.get("src"))
                if img:
                    return img
    return None


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
        _validate_url(rss_url)
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:25]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            # Validate the article link before storing
            try:
                _validate_url(link)
            except ValueError as e:
                log.warning("Skipping feed entry with unsafe URL (%s): %s", e, link[:80])
                continue
            image = _extract_rss_image(entry)
            content = ""
            if hasattr(entry, "summary"):
                content = _sanitize_text(entry.summary)
            elif hasattr(entry, "content") and entry.content:
                content = _sanitize_text(entry.content[0].value)
            published = entry.get("published", entry.get("updated"))
            items.append(FeedItem(
                title=title, url=link, source_name=source_name,
                category=category, image_url=image,
                published_at=published,
                content_snippet=content if content else None,
            ))
        log.info("Fetched %d items from %s", len(items), source_name)
    except ValueError as e:
        log.error("Blocked unsafe RSS source %s: %s", source_name, e)
    except Exception as e:
        log.error("Failed to fetch RSS from %s: %s", source_name, e)
    return items


async def fetch_article_content(url) -> tuple[str | None, str | None]:
    """Fetch article text and og:image URL from the page.

    Returns (content, og_image_url).
    """
    try:
        _validate_url(url)
    except ValueError as e:
        log.warning("Blocked fetch_article_content for unsafe URL: %s", e)
        return (None, None)

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
                candidate = meta["content"].strip()
                try:
                    _validate_url(candidate)
                    og_image = candidate
                except ValueError:
                    pass
                break
        if not og_image:
            for meta in soup.find_all("meta"):
                prop = meta.get("property", "") or meta.get("name", "")
                if prop in ("twitter:image", "twitter:image:src") and meta.get("content"):
                    candidate = meta["content"].strip()
                    try:
                        _validate_url(candidate)
                        og_image = candidate
                    except ValueError:
                        pass
                    break

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.find("div", class_="post-content")
        text = (article or soup).get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)[:8000]
        return (content if len(content) > 100 else None, og_image)
    except Exception as e:
        log.error("Failed to fetch article from %s: %s", url, e)
        return (None, None)
