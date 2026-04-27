"""
EPO OPS API — European Patent Office Open Patent Services.
Free, requires registration at ops.epo.org.
Set env vars: EPO_CLIENT_ID, EPO_CLIENT_SECRET

Registration steps:
1. Go to https://ops.epo.org
2. Click "Register" → create account
3. In your account → "My Apps" → create new app
4. Copy client_id + client_secret → add to .env
"""
import os
import httpx
from xml.etree import ElementTree as ET
from loguru import logger

EPO_AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
EPO_SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"

EPO_CLIENT_ID = os.environ.get("EPO_CLIENT_ID", "")
EPO_CLIENT_SECRET = os.environ.get("EPO_CLIENT_SECRET", "")

EPO_NAMESPACES = {
    "ops": "http://ops.epo.org",
    "epo": "http://www.epo.org/exchange",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def _get_access_token() -> str:
    """OAuth2 client_credentials flow for EPO OPS."""
    if not EPO_CLIENT_ID or not EPO_CLIENT_SECRET:
        raise RuntimeError(
            "EPO_CLIENT_ID and EPO_CLIENT_SECRET not set. "
            "Register at https://ops.epo.org to get credentials."
        )
    with httpx.Client(timeout=20) as client:
        resp = client.post(
            EPO_AUTH_URL,
            data={"grant_type": "client_credentials"},
            auth=(EPO_CLIENT_ID, EPO_CLIENT_SECRET),
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


def search_epo(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Search EPO patents for given terms.
    Returns list of item dicts for scraped_items table.
    Falls back gracefully if credentials not set.
    """
    if not EPO_CLIENT_ID:
        logger.warning("[EPO] No credentials set — skipping EPO search. Register at ops.epo.org")
        return []

    all_items = []

    try:
        token = _get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        logger.error(f"[EPO] Auth failed: {e}")
        return []

    for term in search_terms:
        # Build CQL query: title contains term
        query = f"ti = {term}"
        logger.info(f"[EPO] Searching: {query}")

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    EPO_SEARCH_URL,
                    params={"q": query, "Range": "1-25"},
                    headers=headers,
                )
                resp.raise_for_status()

            root = ET.fromstring(resp.content)

            # Parse XML response
            for doc in root.findall(".//{http://ops.epo.org}exchange-document"):
                doc_num = doc.get("doc-number", "")
                kind = doc.get("kind", "")
                country = doc.get("country", "EP")

                # Title
                title_el = doc.find(".//{http://www.epo.org/exchange}title[@lang='en']")
                if title_el is None:
                    title_el = doc.find(".//{http://www.epo.org/exchange}title")
                title = title_el.text.strip() if title_el is not None else doc_num

                # Abstract
                abstract_el = doc.find(".//{http://www.epo.org/exchange}abstract[@lang='en']//{http://www.epo.org/exchange}p")
                abstract = abstract_el.text.strip() if abstract_el is not None else ""

                # Date
                date_el = doc.find(".//{http://www.epo.org/exchange}publication-reference//{http://www.epo.org/exchange}date")
                pub_date = date_el.text if date_el is not None else None
                if pub_date and len(pub_date) == 8:
                    pub_date = f"{pub_date[:4]}-{pub_date[4:6]}-{pub_date[6:]}T00:00:00Z"

                # Applicant/assignee
                applicant_el = doc.find(".//{http://www.epo.org/exchange}applicant[@sequence='1']//{http://www.epo.org/exchange}name")
                applicant = applicant_el.text.strip() if applicant_el is not None else ""

                url = f"https://worldwide.espacenet.com/patent/search/family/000000000/publication/{country}{doc_num}{kind}"

                all_items.append({
                    "source_name": "EPO — European Patent Office",
                    "category_slug": "patents",
                    "title": title,
                    "url": url,
                    "content": f"Applicant: {applicant}\n\n{abstract}",
                    "language": "en",
                    "published_at": pub_date,
                    "platform": None,
                    "author": applicant,
                })

            logger.info(f"[EPO] '{term}': {len(all_items)} patents")

        except Exception as e:
            logger.error(f"[EPO] Search failed for '{term}': {e}")

    return all_items
