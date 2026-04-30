"""
Article-Direct Scraper — Layer 0.5
For sources where the URL IS the article (not a listing page).
Extracts title + full body text, returns a single scraped_item dict.
Falls back to Playwright for JS-heavy sites (Sohu, Sina, ZDF, etc.).
"""
import asyncio
import re
from typing import Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from loguru import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,de;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_CONTENT_CHARS = 6000

# Domain → ordered list of CSS selectors for article body
CONTENT_SELECTORS: dict[str, list[str]] = {
    "gov.cn":                   [".article-content p", ".pages-content p", "#UCAP-CONTENT p", ".content p"],
    "news.cn":                  ["#detail p", ".article p", ".content p"],
    "xinhuanet.com":            ["#detail p", ".article p"],
    "cppcc.gov.cn":             [".content p", ".artical p", ".article p"],
    "szzg.gov.cn":              [".content p", ".article p"],
    "sohu.com":                 ["#mp-editor p", ".article p", ".text p"],
    "sina.com.cn":              ["#artibody p", ".article p", ".content p"],
    "k.sina.com.cn":            ["#artibody p", ".article p"],
    "finance.sina.com.cn":      ["#artibody p", ".article p"],
    "stcn.com":                 [".article-content p", ".detail-content p"],
    "nongjitong.com":           [".article-content p", ".content p"],
    "czta.org.cn":              [".article-content p", ".content p"],
    "chyxx.com":                [".article_con p", ".article-content p"],
    "hit.edu.cn":               [".content p", ".article p"],
    "cas.cn":                   [".content p", ".text p"],
    # Japanese
    "bio-sta.jp":               [".entry-content p", ".post-content p"],
    "foocom.net":               [".entry-content p", ".post-content p"],
    "affrc.maff.go.jp":         [".section p", ".main p", ".content p"],
    "cbijapan.com":             [".entry-content p", ".content p"],
    "jst.go.jp":                [".content p", ".article p"],
    # German
    "ad-hoc-news.de":           [".article-text p", ".text p"],
    "trendreport.de":           [".entry-content p", ".post-content p"],
    "gvpraxis.food-service.de": [".article-body p", ".content p"],
    "all-ai.de":                [".post-content p", ".entry-content p"],
    "bmleh.de":                 [".content-text p", ".text-block p", ".content p"],
    "zdf.de":                   [".article-body p", ".article__body p"],
    # Israeli / English
    "netafim.com":              [".content-body p", ".rich-text p", ".article-content p"],
    "global-agriculture.com":   [".post-content p", ".entry-content p"],
    "israelagri.com":           [".entry-content p", ".post-content p"],
    "finextra.com":             [".blog-content p", ".article-body p"],
    "geneticliteracyproject.org": [".post-content p", ".entry-content p"],
    "igrownews.com":            [".entry-content p", ".article-body p"],
}

GENERIC_SELECTORS = [
    ".article-body", ".article-content", ".post-content",
    ".entry-content", ".story-body", ".content-body",
    "article .content", "article p",
]

# Sites that need Playwright (heavy JS, SPA, or anti-bot)
JS_HEAVY_DOMAINS = {
    "sohu.com", "sina.com.cn", "k.sina.com.cn", "finance.sina.com.cn",
    "stcn.com", "chyxx.com", "qianzhan.com", "zdf.de",
    # Chinese gov sites load article body via JS
    "gov.cn", "news.cn", "xinhuanet.com", "cppcc.gov.cn", "szzg.gov.cn",
    "hit.edu.cn",
    # Netafim uses a heavy React SPA
    "netafim.com",
}


def _get_domain(url: str) -> str:
    netloc = urlparse(url).netloc.replace("www.", "")
    # Match longest suffix in our dict
    for key in CONTENT_SELECTORS:
        if netloc.endswith(key):
            return key
    return netloc


def _fetch_html_httpx(url: str) -> Optional[str]:
    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.debug(f"[ArticleDirect] httpx failed for {url}: {e}")
        return None


def _fetch_html_playwright(url: str) -> Optional[str]:
    async def _run():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=HEADERS["User-Agent"],
                    ignore_https_errors=True,
                )
                page = await context.new_page()
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,mp4,mp3}",
                    lambda r: r.abort(),
                )
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)
                return await page.content()
            except Exception as e:
                logger.debug(f"[ArticleDirect] Playwright fetch failed for {url}: {e}")
                return None
            finally:
                await browser.close()

    try:
        return asyncio.run(_run())
    except Exception:
        return None


def _extract_title(soup: BeautifulSoup) -> str:
    # 1. og:title meta
    og = soup.find("meta", property="og:title")
    if og and og.get("content", "").strip():
        return og["content"].strip()
    # 2. First <h1>
    h1 = soup.find("h1")
    if h1:
        t = h1.get_text(strip=True)
        if len(t) > 5:
            return t
    # 3. <title> tag (strip site name after " | " or " - " or " — ")
    title_tag = soup.find("title")
    if title_tag:
        t = title_tag.get_text(strip=True)
        for sep in [" | ", " - ", " — ", " – ", " · "]:
            if sep in t:
                t = t.split(sep)[0].strip()
        # Reject if it looks like just a domain name (no spaces, ends with TLD)
        import re as _re
        if len(t) > 5 and not _re.fullmatch(r'[\w.\-]+\.(com|org|net|gov|cn|jp|de|nl|dk|io)', t):
            return t
    return ""


def _extract_content(soup: BeautifulSoup, domain: str) -> str:
    selectors = CONTENT_SELECTORS.get(domain, []) + GENERIC_SELECTORS
    for sel in selectors:
        elements = soup.select(sel)
        if not elements:
            continue
        text = " ".join(el.get_text(separator=" ", strip=True) for el in elements)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 120:
            return text[:MAX_CONTENT_CHARS]
    return ""


def _extract_date(soup: BeautifulSoup) -> Optional[str]:
    # og:article:published_time
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content"):
        return meta["content"]
    # datePublished JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            for key in ("datePublished", "dateCreated", "publishedAt"):
                if data.get(key):
                    return data[key]
        except Exception:
            pass
    return None


def scrape_article_direct(source: dict) -> list[dict]:
    """
    Treat source.url as the article itself. Extract title + content.
    Returns a 1-item list or [] on failure.
    """
    url = source.get("url")
    if not url:
        return []

    domain = _get_domain(url)
    needs_js = any(url.startswith(f"https://{d}") or url.startswith(f"http://{d}")
                   or f".{d}/" in url or f".{d}" == urlparse(url).netloc.replace("www.", "")
                   for d in JS_HEAVY_DOMAINS)

    html = None
    if not needs_js:
        html = _fetch_html_httpx(url)
    if not html:
        logger.debug(f"[ArticleDirect] {source['name']}: using Playwright")
        html = _fetch_html_playwright(url)

    if not html:
        logger.warning(f"[ArticleDirect] {source['name']}: could not fetch HTML")
        return []

    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup)
    if not title:
        logger.warning(f"[ArticleDirect] {source['name']}: no title found")
        return []

    content = _extract_content(soup, domain)
    pub_date = _extract_date(soup)

    logger.info(
        f"[ArticleDirect] {source['name'].encode('ascii', errors='replace').decode()}: "
        f"title={len(title)}ch content={len(content)}ch"
    )
    return [{
        "source_name": source["name"],
        "category_slug": source.get("category_slug", "news"),
        "title": title,
        "url": url,
        "content": content,
        "language": source.get("language", "en"),
        "published_at": pub_date,
        "platform": None,
    }]
