import json
import os
import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv
import httpx
from loguru import logger  # Importing Loguru for logging

# Load environment variables
load_dotenv()

# Initialize clients
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
API_KEY = os.getenv("SERPAPI_API_KEY")

# Loguru configuration to log to a file
logger.add("app.log", level="INFO")  # Log file configuration
class AlertConsolidationError(Exception):
    """Custom exception for alert consolidation errors"""
    pass

async def generate_alerts_llm(all_alerts: List[Dict]) -> List[Dict]:
    """
    Consolidate and deduplicate all alerts from the last 3 days using LLM and return structured results.
    """
    if not all_alerts:
        logger.info("No alerts to process")
        return []

    prompt = f"""
You are an expert in consolidating and deduplicating agricultural news alerts from the last 3 days and returning them in a structured format.

**GOAL:**
Consolidate similar alerts and deduplicate any repetitive entries, with a focus on **tomato-related agriculture**. Ensure that only the most relevant and unique stories are included, while also incorporating broader agricultural news that directly impacts tomato farming and related industries.

**RULES:**
1. **Aggressively remove duplicates or near-duplicates**: If two or more alerts are very similar, consolidate them into a single entry. 
2. **Merge similar alerts**: Combine similar alerts into one summary. This may include combining content from multiple sources if they are reporting on the same event or topic.
3. **Prioritize tomato-related news**: Focus on **tomato crops**, **tomato processing**, **tomato pricing**, and other directly related areas like government schemes or innovations specific to tomatoes. If no tomato-specific content is available, consider other agricultural news that may have an indirect impact on the tomato industry (e.g., agricultural policies, climate effects, etc.).
4. **Include all key information from multiple sources**: If multiple sources report the same event, combine key information into one alert while crediting the sources.
5. **Translate titles to English if necessary**: If the title is not in English, provide a clear translation while maintaining the meaning of the original headline.
6. **Ensure correct categorization**: Categorize each alert under a single relevant category, such as trade, technology, processing, innovation, policy, climate, or pricing. If necessary, use multiple categories for alerts that cover multiple aspects.
7. **Provide the best guess for language and country based on content**: For each alert, determine the original language and country or region of origin, even if not explicitly stated in the content. If the country is not directly mentioned, deduce it from contextual clues.
8. **Be mindful of relevant agricultural news**: If there are broader trends in agriculture, such as new technology or regulations, include them only if they directly impact the tomato industry or tomato farming.

INPUT ALERTS ({len(all_alerts)} total):
{json.dumps(all_alerts, indent=2)}

OUTPUT FORMAT:
Return a pure JSON array, no markdown or extra text. Each item must follow this structure:
[ 
  {{
    "title_translated": "English-translated title of the alert",
    "original_title": "Original title in its original language",
    "summary_en": "Concise summary of the alert in English",
    "source": "Original URL if available, else empty string",
    "language": "Detected language of original alert",
    "country": "Most relevant country or region for the alert",
    "region":"Continent or region that country belongs to"
    "category": "One-word category like trade, technology, climate, policy, etc.",
    "timestamp": "YYYY-MM-DD format or best guess"
  }},
  ...
]
"""

    try:
        logger.info("Sending prompt to OpenAI API...")  # Log the API request
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[ 
                {"role": "system", "content": "You extract structured summaries from tomato-related news in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        # Handle the response
        output_text = response.choices[0].message.content.strip()

        # Check if the output starts with the markdown format for JSON
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()

        if not output_text:
            logger.error("❌ Empty response from OpenAI API.")  # Log the error
            return []

        try:
            # Parse the output text as JSON
            parsed_response = json.loads(output_text)
            logger.info(f"Successfully parsed {len(parsed_response)} stories.")  # Log success
            return parsed_response

        except json.JSONDecodeError as json_error:
            logger.error(f"🔴 JSON parsing error: {json_error}")  # Log JSON parsing error
            logger.debug(f"Raw model output:\n{output_text}")  # Log raw output for debugging
            return []

    except Exception as e:
        logger.error(f"API call failed: {e}")  # Log any general errors
        return []
