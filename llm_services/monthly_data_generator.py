# llm_services/monthly_data_generator.py

import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_monthly_news_summary(news_items):
    """
    Send combined news items to LLM and get top 6 summarized news items for the month.
    """
    if not news_items:
        logger.warning("No news items provided to generate_monthly_news_summary.")
        return []

    prompt = f"""
        You are an agricultural news analyst AI that selects and summarizes the **Top 6 most important tomato-related news stories** from the last month.

        ### GOAL:
        From the provided list of news items, identify the 6 most significant, impactful, or insightful stories about **tomatoes** or **related agricultural developments**, and summarize them concisely in a structured JSON format.

        ### RULES:
        1. **Prioritize importance**: Select news that are most relevant to farmers, traders, agribusinesses, or policy makers in the tomato industry.
        2. **Remove duplicates or near-duplicates**: Merge similar headlines if needed.
        3. **Summarize clearly**: Provide a readable English summary for each news.
        4. **Add metadata**: Return the country, language, category, etc., based on the original news.

        ### INPUT ({len(news_items)} items):
        {json.dumps(news_items, indent=2)}

        ### OUTPUT FORMAT:
        Return a **JSON array with exactly 6 objects**, each using this structure:
        [
        {{
            "title_translated": "English-translated title of the news",
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
                {"role": "system", "content": "You summarize and structure top agriculture alerts about tomatoes for a monthly report."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2500
        )

        output_text = response.choices[0].message.content.strip()
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()

        return json.loads(output_text)
    except Exception as e:
        logger.error(f"Failed to generate monthly news summary: {e}")
        return [] 

async def generate_monthly_technical_data_summary(patents, regulations, genetics):
    """
    Send all patents, regulations, and genetic resources from the last 4 weeks to the LLM
    and get a deduplicated, concise monthly summary for each category.
    """
    if not patents and not regulations and not genetics:
        logger.warning("No technical data provided to generate_monthly_technical_data_summary.")
        return {
            "patents": [],
            "regulations": [],
            "genetic_resources": []
        }

    prompt = f"""
        You are a technical agricultural analyst AI that processes patents, regulations, and genetic resources data related to tomatoes for a **monthly report**.

        ### GOAL:
        From the provided technical data, create clear, informative, and **deduplicated** statements for each category that would be useful for agricultural professionals, researchers, and industry stakeholders. Remove any duplicate or near-duplicate items across the 4 weeks.

        ### RULES:
        1. **Create concise statements**: Each statement should be 1-2 sentences maximum
        2. **Remove duplicates**: If similar or duplicate items exist, merge or summarize them as one.
        3. **Focus on impact**: Highlight what's important for the tomato industry
        4. **Use clear language**: Avoid overly technical jargon
        5. **Maintain accuracy**: Base statements strictly on the provided data

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
                ...
            ],
            "regulations": [
                "Statement about regulation 1",
                ...
            ],
            "genetic_resources": [
                "Statement about genetic resource 1",
                ...
            ]
        }}

        **IMPORTANT**: Return only the JSON object. Do not include any explanation or markdown.
        """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze and summarize technical agricultural data about tomatoes for a monthly report."},
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
        logger.error(f"Failed to generate monthly technical data summary: {e}")
        return {
            "patents": [],
            "regulations": [],
            "genetic_resources": []
        } 

async def generate_monthly_breeding_recommendations(news_data, technical_data, social_media_data):
    """
    Use all monthly data to generate 5 breeding recommendations for tomatoes.
    """
    prompt = f"""
        You are an expert tomato breeding advisor. Given the following data from the past month:
        
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
                {"role": "system", "content": "You generate breeding recommendations for tomatoes using monthly agricultural data."},
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
        logger.error(f"Failed to generate monthly breeding recommendations: {e}")
        return [] 