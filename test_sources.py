"""
Source connectivity and content test.
Tests every RSS and HTML source in config/sources.json.
Skips: apify actors, patent APIs, social platforms (all require separate credentials).

Run: python test_sources.py
"""
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

try:
    import feedparser
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser", "-q"])
    import feedparser

try:
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "-q"])
    from bs4 import BeautifulSoup

CONFIG_PATH = Path(__file__).parent / "config" / "sources.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20


def _get(url: str) -> httpx.Response:
    """GET with browser headers; retries with SSL verify=False on cert errors."""
    try:
        return httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
    except httpx.ConnectError as e:
        if "CERTIFICATE" in str(e).upper() or "SSL" in str(e).upper():
            return httpx.get(url, headers=HEADERS, timeout=TIMEOUT,
                             follow_redirects=True, verify=False)
        raise


def test_rss(source: dict) -> dict:
    feed_url = source.get("rss_url") or source.get("url")
    try:
        resp = _get(feed_url)
        if resp.status_code != 200:
            return {"status": "FAIL", "detail": f"HTTP {resp.status_code}", "items": 0}
        feed = feedparser.parse(resp.text)
        count = len(feed.entries)
        if count == 0:
            return {"status": "EMPTY", "detail": "Feed parsed but 0 entries", "items": 0}
        titles = [e.get("title", "")[:60] for e in feed.entries[:3]]
        return {"status": "OK", "detail": f"{count} entries | {' | '.join(titles)}", "items": count}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)[:80], "items": 0}


def test_html(source: dict) -> dict:
    url = source.get("url", "")
    css = source.get("css_selector", "a")
    try:
        resp = _get(url)
        if resp.status_code != 200:
            return {"status": "FAIL", "detail": f"HTTP {resp.status_code}", "items": 0}
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(css) if css and css != "a" else []
        if not links:
            # Fall back to any <a> with href containing article/news/post patterns
            links = soup.find_all("a", href=lambda h: h and any(
                x in h for x in ["/article", "/news", "/post", "/blog", "/press", "/update", "/release"]
            ))
        count = len(links)
        if count == 0:
            return {"status": "EMPTY", "detail": f"Selector '{css}' found 0 links", "items": 0}
        titles = [l.get_text(strip=True)[:50] or l.get("href", "")[:50] for l in links[:3]]
        return {"status": "OK", "detail": f"{count} links | {' | '.join(titles)}", "items": count}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)[:80], "items": 0}


def test_source(category: str, source: dict) -> dict:
    scrape_type = source.get("scrape_type", "html")
    name = source.get("name", "")

    if scrape_type in ("apify", "api_epo", "api_uspto", "api_cnipa", "praw"):
        return {
            "category": category,
            "name": name,
            "url": source.get("url", ""),
            "type": scrape_type,
            "status": "SKIP",
            "detail": f"Requires external API ({scrape_type})",
            "items": 0,
        }

    t0 = time.time()
    # Respect scrape_type: only try RSS if that's the declared type (or html has no rss_url)
    if scrape_type == "rss":
        result = test_rss(source)
    elif scrape_type == "html":
        result = test_html(source)
        # If HTML got nothing but there's an rss_url, try that as a bonus
        if result["status"] in ("EMPTY", "FAIL", "ERROR") and source.get("rss_url"):
            rss_result = test_rss(source)
            if rss_result["status"] == "OK":
                result = {**rss_result, "detail": "[rss fallback] " + rss_result["detail"]}
    else:
        result = test_html(source)

    elapsed = round(time.time() - t0, 1)
    return {
        "category": category,
        "name": name,
        "url": source.get("rss_url") or source.get("url", ""),
        "type": scrape_type,
        "elapsed": elapsed,
        **result,
    }


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    all_sources = []
    for cat_slug, cat_data in config["categories"].items():
        for src in cat_data.get("sources", []):
            all_sources.append((cat_slug, src))

    print(f"\nTesting {len(all_sources)} sources (parallel, timeout={TIMEOUT}s)\n")
    print(f"{'Category':<14} {'Source':<38} {'Type':<10} {'Status':<7} {'Items':>5}  Detail")
    print("-" * 120)

    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(test_source, cat, src): (cat, src) for cat, src in all_sources}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            status_sym = {"OK": "+", "FAIL": "X", "EMPTY": "~", "ERROR": "!", "SKIP": "-"}.get(r["status"], "?")
            print(
                f"{r['category']:<14} {r['name'][:38]:<38} {r['type']:<10} "
                f"{status_sym} {r['status']:<5} {r['items']:>5}  {r.get('detail','')[:60]}"
            )

    # Summary
    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    empty = [r for r in results if r["status"] == "EMPTY"]
    skip = [r for r in results if r["status"] == "SKIP"]

    print(f"\n{'='*120}")
    print(f"SUMMARY: {len(ok)} OK  |  {len(empty)} EMPTY  |  {len(fail)} FAILED  |  {len(skip)} SKIPPED (API/Apify)")

    if fail:
        print(f"\nFAILED sources:")
        for r in fail:
            print(f"  [{r['category']}] {r['name']}: {r['detail']}")

    if empty:
        print(f"\nEMPTY sources (reachable but no content extracted):")
        for r in empty:
            print(f"  [{r['category']}] {r['name']}: {r['detail']}")


if __name__ == "__main__":
    main()
