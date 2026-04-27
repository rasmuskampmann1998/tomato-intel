import os
import re
import asyncio
from dotenv import load_dotenv
from langchain_community.tools.reddit_search.tool import RedditSearchRun, RedditSearchSchema
from langchain_community.utilities.reddit_search import RedditSearchAPIWrapper
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("app.log", level="INFO")

# Environment credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Reddit search instance (sync)
search = RedditSearchRun(
    api_wrapper=RedditSearchAPIWrapper(
        reddit_client_id=REDDIT_CLIENT_ID,
        reddit_client_secret=REDDIT_CLIENT_SECRET,
        reddit_user_agent=REDDIT_USER_AGENT,
    )
)

def extract_posts(result_text, subreddit):
    posts = []
    split_posts = result_text.strip().split("Post Title:")
    for post_raw in split_posts[1:]:
        try:
            post = {
                "title": re.search(r"'(.*?)'", post_raw).group(1).strip() if re.search(r"'(.*?)'", post_raw) else None,
                "user": re.search(r"User:\s*(.*?)\n", post_raw).group(1).strip() if re.search(r"User:\s*(.*?)\n", post_raw) else None,
                "subreddit": re.search(r"Subreddit:\s*(.*?)\n", post_raw).group(1).strip() if re.search(r"Subreddit:\s*(.*?)\n", post_raw) else subreddit,
                "body": re.search(r"Text body:\s*(.*?)\n\s*Post URL:", post_raw, re.DOTALL).group(1).strip() if re.search(r"Text body:\s*(.*?)\n\s*Post URL:", post_raw, re.DOTALL) else None,
                "url": re.search(r"Post URL:\s*(.*?)\n", post_raw).group(1).strip() if re.search(r"Post URL:\s*(.*?)\n", post_raw) else None
            }
            posts.append(post)
        except Exception as e:
            logger.warning(f"❌ Failed to parse post block: {e}")
    return posts

def _sync_reddit_scrape():
    time_filters = ["day"]
    sort_options = ["top", "relevance"]

    # Expanded agriculture-related subreddits
    subreddits = [
        "agriculture", "farming", "gardening", "homestead", "organicgardening",
        "horticulture", "greenhouse_gardening", "cropfarming", "urbanfarming"
    ]

    # Expanded tomato-related queries
    tomato_queries = [
        "tomato", "tomatoes", "cherry tomato", "roma tomato", "heirloom tomato",
        "tomato pruning", "tomato trellis", "tomato disease", "tomato pest",
        "tomato care", "tomato fertilizer", "tomato yield", "tomato harvest",
        "tomato hybrid", "tomato variety"
    ]

    structured_posts = []
    logger.info("Starting Reddit post scraping using LangChain RedditSearchAPIWrapper.")

    for subreddit in subreddits:
        for query in tomato_queries:
            for time_filter in time_filters:
                for sort in sort_options:
                    try:
                        params = RedditSearchSchema(
                            query=query,
                            sort=sort,
                            time_filter=time_filter,
                            subreddit=subreddit,
                            limit="10"
                        )
                        result_text = search.run(tool_input=params.model_dump())
                        if "found" in result_text and "Post Title" in result_text:
                            extracted = extract_posts(result_text, subreddit)
                            structured_posts.extend(extracted)
                            logger.info(f"Extracted {len(extracted)} posts from {subreddit} | Query: {query} | Sort: {sort} | Time: {time_filter}")
                        else:
                            logger.debug(f"No relevant posts in {subreddit} | Query: {query} | Sort: {sort} | Time: {time_filter}")
                    except Exception as e:
                        logger.warning(f"Error during scraping: {subreddit} | {query} | {sort} | {time_filter} | {e}")

    # Deduplicate based on post URL
    unique_posts = {post["url"]: post for post in structured_posts if post["url"]}
    logger.info(f"Total unique Reddit posts fetched: {len(unique_posts)}")
    return list(unique_posts.values())

async def get_latest_reddit_data():
    """
    Run the Reddit scraping safely in async environments using a thread.
    """
    return await asyncio.to_thread(_sync_reddit_scrape)
