"""
EPO OPS API — European Patent Office Open Patent Services.
Free, requires registration at ops.epo.org.
Set env vars: EPO_CLIENT_ID, EPO_CLIENT_SECRET
"""
import os
import httpx
from loguru import logger

EPO_AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
EPO_SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"
EPO_BIBLIO_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc"

EPO_CLIENT_ID = os.environ.get("EPO_CLIENT_ID", "")
EPO_CLIENT_SECRET = os.environ.get("EPO_CLIENT_SECRET", "")


def _get_access_token() -> str:
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


def _get_doc_ids(token: str, query: str, max_results: int = 25) -> list[dict]:
    """Get publication references from search. Returns list of {doc_id, family_id}."""
    try:
        resp = httpx.get(
            EPO_SEARCH_URL,
            params={"q": query, "Range": f"1-{max_results}"},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results = (
            data.get("ops:world-patent-data", {})
            .get("ops:biblio-search", {})
            .get("ops:search-result", {})
            .get("ops:publication-reference", [])
        )
        if isinstance(results, dict):
            results = [results]
        out = []
        for r in results:
            doc_id = r.get("document-id", {})
            if isinstance(doc_id, list):
                doc_id = next((d for d in doc_id if d.get("@document-id-type") == "docdb"), doc_id[0])
            country = doc_id.get("country", {}).get("$", "EP")
            num = doc_id.get("doc-number", {}).get("$", "")
            kind = doc_id.get("kind", {}).get("$", "A")
            family_id = r.get("@family-id", "")
            if num:
                out.append({"epodoc": f"{country}{num}", "country": country, "num": num, "kind": kind, "family_id": family_id})
        return out
    except Exception as e:
        logger.error(f"[EPO] Search failed for {query!r}: {e}")
        return []


def _fetch_biblio(token: str, epodoc: str) -> dict:
    """Fetch title, abstract, applicant for one patent."""
    try:
        resp = httpx.get(
            f"{EPO_BIBLIO_URL}/{epodoc}/biblio",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20,
        )
        if resp.status_code != 200:
            return {}
        data = resp.json()
        exch_docs = (
            data.get("ops:world-patent-data", {})
            .get("exchange-documents", {})
            .get("exchange-document", {})
        )
        if isinstance(exch_docs, list):
            exch_docs = exch_docs[0]

        # Title
        titles = exch_docs.get("bibliographic-data", {}).get("invention-title", [])
        if isinstance(titles, dict):
            titles = [titles]
        title = next((t.get("$", "") for t in titles if t.get("@lang") == "en"), "")
        if not title and titles:
            title = titles[0].get("$", "")

        # Abstract
        abstracts = exch_docs.get("abstract", [])
        if isinstance(abstracts, dict):
            abstracts = [abstracts]
        abstract = next((a.get("p", {}).get("$", "") for a in abstracts if a.get("@lang") == "en"), "")
        if not abstract and abstracts:
            p = abstracts[0].get("p", {})
            abstract = p.get("$", "") if isinstance(p, dict) else ""

        # Applicant
        applicants = (
            exch_docs.get("bibliographic-data", {})
            .get("parties", {})
            .get("applicants", {})
            .get("applicant", [])
        )
        if isinstance(applicants, dict):
            applicants = [applicants]
        applicant = next(
            (a.get("applicant-name", {}).get("name", {}).get("$", "")
             for a in applicants if a.get("@sequence") == "1"),
            ""
        )

        # Date
        pub_ref = (
            exch_docs.get("bibliographic-data", {})
            .get("publication-reference", {})
            .get("document-id", {})
        )
        if isinstance(pub_ref, list):
            pub_ref = next((d for d in pub_ref if d.get("@document-id-type") == "epodoc"), pub_ref[0])
        raw_date = pub_ref.get("date", {}).get("$", "")
        pub_date = None
        if raw_date and len(raw_date) == 8:
            pub_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}T00:00:00Z"

        return {"title": title, "abstract": abstract, "applicant": applicant, "pub_date": pub_date}
    except Exception as e:
        logger.debug(f"[EPO] Biblio fetch failed for {epodoc}: {e}")
        return {}


def search_epo(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Search EPO patents for given terms.
    Returns list of item dicts for scraped_items table.
    """
    if not EPO_CLIENT_ID:
        logger.warning("[EPO] No credentials — skipping. Register at ops.epo.org")
        return []

    try:
        token = _get_access_token()
    except Exception as e:
        logger.error(f"[EPO] Auth failed: {e}")
        return []

    all_items = []
    seen_family_ids = set()

    for term in search_terms:
        query = f"ta = {term}"
        logger.info(f"[EPO] Searching: {query}")
        doc_refs = _get_doc_ids(token, query, max_results=10)

        count = 0
        for ref in doc_refs:
            family_id = ref.get("family_id", "")
            if family_id and family_id in seen_family_ids:
                continue
            if family_id:
                seen_family_ids.add(family_id)

            biblio = _fetch_biblio(token, ref["epodoc"])
            title = biblio.get("title") or ref["epodoc"]
            if not title or len(title) < 5:
                continue

            applicant = biblio.get("applicant", "")
            abstract = biblio.get("abstract", "")
            pub_date = biblio.get("pub_date")
            epodoc = ref["epodoc"]

            all_items.append({
                "source_name": "EPO — European Patent Office",
                "category_slug": "patents",
                "title": title,
                "url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{epodoc}",
                "content": f"Applicant: {applicant}\n\n{abstract}",
                "language": "en",
                "published_at": pub_date,
                "platform": None,
                "author": applicant,
            })
            count += 1

        logger.info(f"[EPO] '{term}': {count} patents")

    return all_items
