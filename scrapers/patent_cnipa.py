"""
CNIPA (China) + IP India patent scrapers.
Both use Apify since their portals are JS-heavy government sites.
CNIPA also searches Google Patents with country filter as a reliable fallback.
"""
import os
from apify_client import ApifyClient
from loguru import logger

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")


def _get_client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_API_TOKEN not set")
    return ApifyClient(APIFY_TOKEN)


def search_cnipa(search_terms: list[str]) -> list[dict]:
    """
    Search Chinese patents via Google Patents (country=CN filter).
    More reliable than scraping CNIPA portal directly.
    """
    all_items = []

    for term in search_terms:
        logger.info(f"[CNIPA] Searching Google Patents for CN: {term}")
        try:
            client = _get_client()
            # Use Google Patents with assignee_country=CN
            search_url = f"https://patents.google.com/patent/search?q={term.replace(' ', '+')}&assignee=&country=CN&before=&after=20200101"

            run_input = {
                "startUrls": [{"url": search_url}],
                "maxCrawlPages": 3,
                "maxCrawlDepth": 0,
                "pageFunction": """
async function pageFunction(context) {
    const { $, request, log } = context;
    const items = [];
    $('search-result-item').each((i, el) => {
        const titleEl = $(el).find('[data-proto="RESULT_TITLE"]');
        const linkEl = $(el).find('a[href*="/patent/"]').first();
        const title = titleEl.text().trim();
        const href = linkEl.attr('href');
        if (title && href) {
            items.push({
                title: title,
                url: 'https://patents.google.com' + href,
                assignee: $(el).find('[data-proto="ASSIGNEE"]').text().trim(),
                date: $(el).find('[data-proto="PUBLICATION_DATE"]').text().trim(),
            });
        }
    });
    return items;
}
""",
                "proxyConfiguration": {"useApifyProxy": True},
            }

            run = client.actor("apify/web-scraper").call(run_input=run_input)
            results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            for r in results:
                title = r.get("title", "")
                url = r.get("url", "")
                if not title or not url:
                    continue
                all_items.append({
                    "source_name": "CNIPA — China Patent Office",
                    "category_slug": "patents",
                    "title": title,
                    "url": url,
                    "content": f"Assignee: {r.get('assignee', '')}",
                    "language": "zh",
                    "published_at": None,
                    "platform": None,
                    "author": r.get("assignee", ""),
                })

            logger.info(f"[CNIPA] '{term}': {len(results)} patents")

        except Exception as e:
            logger.error(f"[CNIPA] Failed for '{term}': {e}")

    return all_items


def search_ip_india(search_terms: list[str]) -> list[dict]:
    """
    Search IP India patent database via Apify.
    Portal: https://iprsearch.ipindia.gov.in/PatentSearch
    """
    all_items = []

    for term in search_terms:
        logger.info(f"[IP India] Searching for: {term}")
        try:
            client = _get_client()
            search_url = f"https://iprsearch.ipindia.gov.in/PatentSearch/PatentSearch/ApplicationNumberSearch"

            run_input = {
                "startUrls": [{"url": search_url}],
                "maxCrawlPages": 2,
                "maxCrawlDepth": 0,
                "pageFunction": """
async function pageFunction(context) {
    const { $, request, log, jQuery } = context;
    // IP India is a form-based search; extract any visible patent rows
    const items = [];
    $('table tr').each((i, row) => {
        const cells = $(row).find('td');
        if (cells.length >= 3) {
            const appNum = $(cells[0]).text().trim();
            const title = $(cells[1]).text().trim() || $(cells[2]).text().trim();
            if (appNum && title && title.length > 5) {
                items.push({ app_number: appNum, title: title });
            }
        }
    });
    return items;
}
""",
                "proxyConfiguration": {"useApifyProxy": True},
            }

            run = client.actor("apify/web-scraper").call(run_input=run_input)
            results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            for r in results:
                title = r.get("title", "")
                app_num = r.get("app_number", "")
                if not title:
                    continue
                all_items.append({
                    "source_name": "IP India",
                    "category_slug": "patents",
                    "title": title,
                    "url": f"https://iprsearch.ipindia.gov.in/PatentSearch/PatentSearch/ViewApplicationStatus?ApplicationNumber={app_num}",
                    "content": f"Application: {app_num}",
                    "language": "en",
                    "published_at": None,
                    "platform": None,
                    "author": "",
                })

            logger.info(f"[IP India] '{term}': {len(results)} patents")

        except Exception as e:
            logger.error(f"[IP India] Failed for '{term}': {e}")

    return all_items
