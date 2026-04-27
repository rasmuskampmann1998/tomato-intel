import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger  # Importing Loguru for logging

# Load API key
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Loguru configuration
logger.add("app.log", level="INFO")  # Log file configuration

async def generate_alert_detail_llm(text: str) -> List[Dict]:
    """
    Extract and structure tomato-related stories from agricultural news, returning a JSON format.
    """
    prompt = f"""
    You are a global agricultural news analyst, specializing in the analysis of agricultural trends and innovations.

    From the following text, extract only the stories that are directly related to **Tomato crops** or **tomato-based agriculture**, as well as closely related agricultural topics. The stories should include details on the following areas:

    1. Tomato farming practices, processing, packaging, export/import activities, pricing, and market dynamics.
    2. Government schemes, regulations, and policies specifically related to tomatoes or the agricultural sector in general.
    3. Innovations in tomato seed development, agricultural biotechnology, or scientific advancements in tomato cultivation.
    4. Any other agricultural topics relevant to the wider industry but focusing on the tomato sector, such as sustainability, climate adaptation, or industry news affecting tomato production.

    The stories can come from any region (Europe, Asia, Americas, Africa, etc.), but **tomato-related content should be prioritized**.

    For each relevant story, extract the following structured information:

    1. **title_translated**: Translate the title into English (or extract and translate the main headline from the story).
    2. **summary_en**: Write a one-sentence summary of the event in English, focusing on tomato-related content but also noting relevant agricultural context where necessary.
    3. **source_url**: Provide the source link (if available), else use an empty string.
    4. **language**: Original language of the news story.
    5. **country**: The country or region most relevant to the alert.
    6. **continent**: The continent the country belongs to (e.g., Europe, Asia).
    7. **category**: One-word category like trade, technology, climate, policy, disease, pricing, etc.
    8. **timestamp**: Use YYYY-MM-DD format. If no date is available, use today's date.

    ### Prioritization:
    - **Tomato-related content** should always be the top priority. Ensure the focus is on **tomato crops**, **tomato-related industry**, and **agricultural innovations impacting tomatoes**.
    - If **tomato-related content** is not available, you may consider **related agricultural content** with a direct link to tomato production or processing (e.g., agricultural policy, sustainable farming practices, climate resilience in agriculture, etc.).

    ### Output Format:
    Respond with valid JSON only using this structure:

    OUTPUT FORMAT:
    [
      {{
        "title_translated": "Translated English title of the alert",
        "summary_en": "One-line summary of the tomato-related event in English",
        "source": "https://link.com or empty string",
        "language": "original_language",
        "country": "relevant_country",
        "Continent":"Continent the country belongs to"
        "category": "one_word_category",
        "timestamp": "YYYY-MM-DD"
      }},
      ...
    ]

    Analyze this content carefully and only output valid JSON:
    \"\"\"{text}\"\"\"    
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
