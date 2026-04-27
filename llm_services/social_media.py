import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger

# Load OpenAI API key from environment variables
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure Loguru logging if not already set
logger.add("app.log", level="INFO")


async def process_reddit_posts(raw_posts: list):
    """
    Use OpenAI GPT-4o to filter Reddit posts.
    Keeps only:
    - Posts related to agriculture or tomato
    - Posts from the last 3 days
    """
    if not raw_posts:
        logger.warning("🚫 No Reddit posts to process.")
        return []


    prompt = f"""
You are an AI assistant for an agriculture intelligence platform.

Analyze the following Reddit posts and **filter strictly**:
- Only include posts clearly related to **agriculture**, **farming**, **horticulture**, **gardening**, or **tomatoes** (e.g. tomato varieties, diseases, yield, harvest, plant care, etc.).
- **Exclude** memes, jokes, casual conversation, or unrelated content (e.g. general food, personal stories, or vague comments).
- Only include posts that are **informative**, **question-based**, or **discussion-driven** about tomato or agricultural practices.
- Discard any post missing required fields (title, user, subreddit, body, url, or date).

Return ONLY a valid JSON **array of objects**, where each object contains:
- title
- user
- subreddit
- body
- url
- date

Do not return markdown, text, explanations, or any wrapper.
Only output a clean JSON array like:
[
  {{
    "title": "Example",
    "user": "username",
    "subreddit": "r/example",
    "body": "content here",
    "url": "https://example.com",
    "date": "2025-06-30"
  }},
  ...
]

Here is the input:
{json.dumps(raw_posts)}
    """

    try:
        logger.info("💬 Sending Reddit filter prompt to OpenAI...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI that returns only clean JSON arrays with no extra text or formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=3000
        )

        content = response.choices[0].message.content.strip()

        # Remove code block markers if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Fix common issue: multiple objects not inside array
        if content.startswith("{") and content.endswith("}"):
            content = f"[{content}]"

        # Ensure it is a proper JSON array
        if not content.startswith("["):
            logger.warning("LLM response is not a JSON array. Attempting to fix.")
            content = f"[{content}]"

        try:
            json_data = json.loads(content)

            if isinstance(json_data, list):
                logger.success(f"Successfully filtered Reddit posts via OpenAI. Total: {len(json_data)}")
                return json_data
            else:
                logger.error("Unexpected structure: JSON is not an array.")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            logger.debug(f"Raw content: {content[:1000]}")
            return []

    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return []
    
