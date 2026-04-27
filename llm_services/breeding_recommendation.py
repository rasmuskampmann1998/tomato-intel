import json
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger  # Importing Loguru for logging

# Load API key
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure Loguru logging
logger.add("app.log", level="INFO")  # Logging to 'app.log' file with INFO level

async def generate_breeding_recommendations_llm() -> dict:
    """
    Generate detailed and comprehensive tomato breeding recommendations for the top 5 varieties.
    First, identify top-performing varieties from the last 5 years, then generate detailed recommendations for each variety.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Generating breeding recommendations for top tomato varieties as of {current_date}")

    prompt = f"""
    You are an expert agricultural advisor specializing in tomato breeding with access to the latest global agricultural innovations and market data for {current_date}.
    
    IMPORTANT: Your response MUST be ONLY valid JSON format. Do not include any markdown formatting, explanations, or text outside the JSON structure.
    
    STEP 1: First, identify the TOP 5 GLOBALLY FAMOUS TOMATO VARIETIES that are most commonly grown worldwide in commercial farming (2020-2025).
    
    Use these specific criteria and research sources:
    
    RESEARCH METHODOLOGY:
    - Analyze global agricultural statistics and commercial farming data
    - Review major seed company catalogs (Monsanto, Syngenta, Bayer, etc.)
    - Check agricultural extension services from major tomato-producing countries (USA, China, India, Turkey, Italy)
    - Reference peer-reviewed agricultural journals and university research publications
    - Examine export/import data for tomato varieties globally
    
    SELECTION CRITERIA (in order of importance):
    1. **Global Commercial Production Volume**: Varieties with highest acreage worldwide
    2. **Seed Sales Data**: Most purchased varieties by farmers globally
    3. **Geographic Distribution**: Varieties grown across multiple continents
    4. **Market Stability**: Varieties consistently grown for 5+ years
    5. **Yield Performance**: Proven high yields (15,000+ kg per acre)
    6. **Disease Resistance**: Strong resistance to major tomato diseases
    7. **Processing Industry Adoption**: Used by major food processing companies
    8. **Climate Adaptability**: Successful in diverse climate zones
    
    FOCUS ON THESE VARIETY CATEGORIES:
    - **Fresh Market Varieties**: Round/slicing tomatoes for fresh consumption
    - **Processing Varieties**: Paste/sauce tomatoes for industrial processing  
    - **Greenhouse Varieties**: High-tech controlled environment production
    - **Specialty Varieties**: Cherry, roma, or unique market tomatoes
    
    EXCLUDE:
    - Rare heirloom varieties with limited commercial production
    - Regional varieties grown only in specific countries/areas
    - Experimental or newly released varieties without proven track record
    - Varieties with declining market share
    
    STEP 2: Generate comprehensive breeding recommendations using the EXACT JSON structure below.
    
    RESPOND WITH ONLY THIS JSON STRUCTURE (no additional text, markdown, or explanations):
    
    {{
        "breeding_recommendation": [
            {{
                "crop": "[Name of Top Variety 1]",
                "variety_characteristics": {{
                    "scientific_name": "Detailed scientific classification",
                    "origin": "Where this variety was developed",
                    "key_traits": ["List 4-5 key distinguishing traits"],
                    "market_position": "Current market status and popularity"
                }},
                "season": "Suitable season on which this variety grows . Example like Summer , winter autumn like this ",
                "top_growing_location": "Regions or location where this variety is most commonly grown like central africa , asia and this type of location not country or state name ",
                "recommended_breeding_strategies": [
                    "6-7 detailed modern breeding strategies specific to this variety",
                    "Include recent innovations in hybridization and genetic selection"
                ],
                "recommended_seed_varieties": [
                    "List 6-7 latest high-performance sub-varieties or hybrids",
                    "Include disease-resistant and climate-adapted versions"
                ],
                "suitable_soil": "Detailed soil requirements specific to this variety with modern soil management techniques also what nutrition that soil should hold ",
                "ideal_temperature": "Optimal planting and harvesting temperature range for this specific variety",
                "sowing_to_harvest_duration_days": "Realistic timeline for this variety (e.g., '75-110 days')",
                "budget_recommendation_estimated": {{
                    "breakdown": {{
                    "labor": "[estimated labor cost] USD",
                    "seeds": "[estimated seed cost] USD",
                    "equipment": "[estimated equipment cost] USD",
                    "irrigation": "[estimated irrigation cost] USD",
                    "pesticides": "[estimated pesticide cost] USD",
                    "fertilizers": "[estimated fertilizer cost] USD"
                    }},
                    "total_budget_estimated": "[total estimated budget] USD"
                }},
                "equipment_needed": [
                    "List 5-7 essential equipment items specific to this variety"
                ],
                "planting_technique": "Detailed planting techniques specific to this variety's requirements",
                "irrigation_guidance": "Advanced irrigation methods tailored to this variety's water needs",
                "fertilizer_plan": "Comprehensive fertilizer program specific to this variety's nutrient requirements",
                "pest_disease_management": "Variety-specific pest and disease management strategies",
                "harvesting_guidance": "Professional harvesting techniques specific to this variety",
                "expected_yield_kg_per_acre": "[realistic yield based on global data for this variety]",
                "expected_roi_usd_per_acre": "[estimated ROI based on yield, input costs, and as per current market price]"
                "market_price_range_usd_per_kg": "Current market price ranges for this specific variety",
                "recommended_selling_channels": [
                    "4-5 selling channels best suited for this variety"
                ],
                "regulatory_compliance_notes": "Regulatory requirements specific to this variety",
                "additional_notes": "Expert tips specific to this variety with latest research findings"
            }},
            {{}}
        ],
        "research_methodology": "Brief explanation of how you identified the top 5 varieties",
        "global_market_overview": "Current global tomato variety market trends and insights"
    }}
    """

    try:
        logger.info("Sending prompt to OpenAI API...")  # Log the API request
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are an expert agricultural advisor specializing in modern tomato breeding. You MUST respond with ONLY valid JSON format. Do not include any markdown formatting, explanations, or text outside the JSON structure."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=6000  # Increased token limit to accommodate 5 varieties
        )

        content = response.choices[0].message.content.strip()

        # More robust JSON extraction
        try:
            # Clean up content to extract JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Find the first { and last } to extract the JSON part
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]
            
            # Ensure that content is valid JSON
            if not content or len(content) < 10:
                logger.error(f"❌ Content too short or empty after cleanup: {content}")
                return None
            
            # Parse JSON
            breeding_recommendations = json.loads(content)
            logger.info("✅ Successfully generated breeding recommendations")
            return breeding_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"⚠️ JSON Parsing Error: {e}")
            logger.error(f"Raw content (first 500 chars): {content[:500]}")
            logger.error(f"Raw content (last 100 chars): {content[-100:]}")
            return None

    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
        return None
