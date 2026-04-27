# llm_services/weekly_data_generator.py

import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_news_summary(alerts):
    """
    Send last 2 alerts to LLM and get top 5 summarized news items.
    """
    if not alerts:
        logger.warning("No alerts provided to generate_news_summary.")
        return []

    prompt = f"""
        You are an agricultural news analyst AI that selects and summarizes the **Top 5 most important tomato-related news stories** from the last week.

        ### GOAL:
        From the provided list of alerts, identify the 5 most significant, impactful, or insightful stories about **tomatoes** or **related agricultural developments**, and summarize them concisely in a structured JSON format.

        ### RULES:
        1. **Prioritize importance**: Select alerts that are most relevant to farmers, traders, agribusinesses, or policy makers in the tomato industry.
        2. **Remove duplicates or near-duplicates**: Merge similar headlines if needed.
        3. **Summarize clearly**: Provide a readable English summary for each news.
        4. **Add metadata**: Return the country, language, category, etc., based on the original alert.

        ### INPUT ({len(alerts)} items):
        {json.dumps(alerts, indent=2)}

        ### OUTPUT FORMAT:
        Return a **JSON array with exactly 5 objects**, each using this structure:
        [
        {{
            "title_translated": "English-translated title of the alert",
            "original_title": "Original title in its original language",
            "summary_en": "Concise summary in English",
            "source": "Original news source URL",
            "language": "Detected language",
            "country": "Country of origin",
            "region": "Continent or region",
            "category": "One-word category (policy, technology, disease, etc.)",
            "timestamp": "YYYY-MM-DD"
        }},
        ...
        ]
        Return only the JSON. Do not include any explanation or markdown.
        """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You summarize and structure top agriculture alerts about tomatoes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        output_text = response.choices[0].message.content.strip()
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()

        return json.loads(output_text)
    except Exception as e:
        logger.error(f"Failed to generate news summary: {e}")
        return []


async def generate_technical_data_summary(patents, regulations, genetics):
    """
    Send latest 3 patents, 3 regulations, and 3 genetic resources to LLM 
    and get formatted statements for each category.
    """
    if not patents and not regulations and not genetics:
        logger.warning("No technical data provided to generate_technical_data_summary.")
        return {
            "patents": [],
            "regulations": [],
            "genetic_resources": []
        }

    prompt = f"""
        You are a technical agricultural analyst AI that processes patents, regulations, and genetic resources data related to tomatoes.

        ### GOAL:
        From the provided technical data, create clear, informative statements for each category that would be useful for agricultural professionals, researchers, and industry stakeholders.

        ### RULES:
        1. **Create concise statements**: Each statement should be 1-2 sentences maximum
        2. **Focus on impact**: Highlight what's important for the tomato industry
        3. **Use clear language**: Avoid overly technical jargon
        4. **Maintain accuracy**: Base statements strictly on the provided data

        ### INPUT DATA:
        **PATENTS ({len(patents)} items):**
        {json.dumps(patents, indent=2)}

        **REGULATIONS ({len(regulations)} items):**
        {json.dumps(regulations, indent=2)}

        **GENETIC RESOURCES ({len(genetics)} items):**
        {json.dumps(genetics, indent=2)}

        ### OUTPUT FORMAT:
        Return a JSON object with exactly this structure:
        {{
            "patents": [
                "Statement about patent 1",
                "Statement about patent 2", 
                "Statement about patent 3"
            ],
            "regulations": [
                "Statement about regulation 1",
                "Statement about regulation 2",
                "Statement about regulation 3"
            ],
            "genetic_resources": [
                "Statement about genetic resource 1",
                "Statement about genetic resource 2",
                "Statement about genetic resource 3"
            ]
        }}

        **IMPORTANT**: Return only the JSON object. Do not include any explanation or markdown.
        """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze and summarize technical agricultural data about tomatoes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        output_text = response.choices[0].message.content.strip()
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()

        return json.loads(output_text)
    except Exception as e:
        logger.error(f"Failed to generate technical data summary: {e}")
        return {
            "patents": [],
            "regulations": [],
            "genetic_resources": []
        }

async def generate_breeding_recommendations(news_data, technical_data, social_media_data):
    """
    Use all weekly data to generate 5 breeding recommendations for tomatoes.
    """
    prompt = f"""
        You are an expert tomato breeding advisor. Given the following data from the past week:
        
        - News data: {json.dumps(news_data, indent=2)}
        - Technical data: {json.dumps(technical_data, indent=2)}
        - Social media data: {json.dumps(social_media_data, indent=2)}

        Analyze all the information and provide 5 actionable, evidence-based recommendations for tomato breeding programs. Each recommendation should be concise, practical, and reference the relevant data (news, technical, or social).

        ### OUTPUT FORMAT:
        Return a JSON array of 5 recommendation strings, like this:
        [
          "First recommendation.",
          "Second recommendation.",
          "Third recommendation.",
          "Fourth recommendation.",
          "Fifth recommendation."
        ]
        Return only the JSON array. Do not include any explanation or markdown.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You generate breeding recommendations for tomatoes using weekly agricultural data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        output_text = response.choices[0].message.content.strip()
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()
        return json.loads(output_text)
    except Exception as e:
        logger.error(f"Failed to generate breeding recommendations: {e}")
        return []