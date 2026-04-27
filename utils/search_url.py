import asyncio
from typing import Optional
import httpx
from dotenv import load_dotenv
import os
from loguru import logger

logger.add("app.log", level="INFO") 

load_dotenv()
API_KEY = os.getenv("SERPAPI_API_KEY")

class AlertConsolidationError(Exception):
    """Custom exception for alert consolidation errors"""
    pass

async def search_article_url(query: str, max_retries: int = 3) -> Optional[str]:
    """
    Search for a news article using SerpAPI and get the URL for a news story based on query.
    Returns only the most relevant link based on content matching.
    
    Args:
        query: The news query string (title translated)
        max_retries: Maximum number of retry attempts
    
    Returns:
        URL of the most relevant search result or None if not found
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to search_article_url")
        return None
    
    params = {
        "q": query.strip(),
        "api_key": API_KEY,
        "engine": "google",
        "num": 10,  # Get more results to find the most relevant one
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Searching for article: {query[:100]}...")
                response = await client.get("https://serpapi.com/search", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check organic results first
                    organic_results = result.get("organic_results", [])
                    if organic_results:
                        # If the title matches, pick the first link
                        for organic_result in organic_results:
                            title = organic_result.get('title', '').lower()
                            if query.lower() in title:  # Simple string match
                                url = organic_result.get('link')
                                if url:
                                    logger.info(f"Found relevant article URL: {url}")
                                    return url
                    
                    # Fallback: if no exact match, return the first organic link
                    if organic_results:
                        first_result = organic_results[0]
                        url = first_result.get("link")
                        if url:
                            logger.info(f"Found article URL (fallback): {url}")
                            return url
                    
                    logger.warning(f"No search results found for query: {query[:100]}")
                    return None

                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue

                else:
                    logger.error(f"SerpAPI error {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    return None

        except httpx.TimeoutException:
            logger.error(f"Timeout occurred on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return None
        except Exception as e:
            logger.error(f"Unexpected error in search_article_url on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return None

    return None


async def process_and_get_sources(news_data: list) -> list:
    """
    Process the given news data to get the source URLs for each entry based on their translated title.
    
    Args:
        news_data: List of dictionaries containing the news details
    
    Returns:
        Updated list with source URLs added
    """
    updated_news_data = []
    
    for alert in news_data:
        title_translated = alert.get("title_translated", "")
        
        if title_translated:
            logger.info(f"Searching for URL for: {title_translated}")
            article_url = await search_article_url(title_translated)
            if article_url:
                alert["source"] = article_url
            else:
                alert["source"] = ""
        
        updated_news_data.append(alert)
    
    return updated_news_data