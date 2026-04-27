import os, json
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger  # Importing Loguru for logging

# Load API key
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add Loguru configuration to log into app.log
logger.add("app.log", level="INFO")  # Log file configuration


async def generate_competitor_data_llm(text_blocks: list) -> dict:
    """
    Accepts a list of plain texts, each from a different company.
    Returns a single JSON structure with an array under 'competitor_data', including market analysis and capture information.
    Enhanced with accurate market data and 5-year historical trends.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Combine all the competitor texts into a single prompt to send to the LLM
    combined_text = "\n\n".join(
        f"---\nCOMPANY: {b['name']}\nURL: {b['url']}\n\nTEXT:\n{b['text']}" for b in text_blocks
    )

    # Construct the enhanced prompt for LLM with accurate market data
    prompt = f"""
You are an expert in agricultural market intelligence with access to detailed information about global agriculture companies as of {today}.

TASK:
Your task is to analyze and generate structured data about **top agriculture companies** (e.g., Syngenta, Bayer, Rijk Zwaan, Corteva, BASF, Groupe Limagrain, etc.).

**CRITICAL MARKET DATA REQUIREMENTS:**
- Use REALISTIC and CURRENT market figures based on 2025 data
- Global Seeds Market: $76.86B (2025) → $99.94B (2030) at 5.39% CAGR
- Global Agriculture Market: $15.5T (2025) → $20.63T (2029) at 7.4% CAGR
- Agricultural Technology Market: $25.36B (2024) → Growing at 13.9% CAGR
- Seed Treatment Market: $9.06B (2025) → $11.87B (2030) at 5.57% CAGR

For each company object, follow this **strict order** and **structure**:

1. **Company Name**:
   - The **company_name**: "<name>"

2. **Company Profile**:
   - "profile": {{
       "link": "<company_website_url>",
       "category": "Agriculture Company",
       "location": "<headquarters_location>",
       "description": "<comprehensive_description_focusing_on_innovation_and_market_position>",
       "services": ["<service1>", "<service2>", "<service3>", "<service4>"],
       "product_lines": ["<product1>", "<product2>", "<product3>", "<product4>"],
       "technologies": ["<tech1>", "<tech2>", "<tech3>"],
       "focus_areas": ["<focus_area1>", "<focus_area2>", "<focus_area3>"]
   }}

3. **Target Audience**:
   - "target_audience": [
       {{
           "group": "Farmers",
           "description": "<Description focusing on yield optimization, crop protection, and sustainable farming solutions>"
       }},
       {{
           "group": "Breeders",
           "description": "<Description focusing on genetics, breeding programs, and variety development>"
       }},
       {{
           "group": "Scientists",
           "description": "<Description focusing on R&D partnerships, biotechnology, and innovation>"
       }},
       {{
           "group": "Researchers",
           "description": "<Description focusing on academic collaborations and research initiatives>"
       }}
   ]

4. **SWOT Analysis**:
   - "swot": {{
       "strengths": ["<strength1>", "<strength2>", "<strength3>", "<strength4>", "<strength5>", "<strength6>"],
       "weaknesses": ["<weakness1>", "<weakness2>", "<weakness3>", "<weakness4>"],
       "opportunities": ["<opportunity1>", "<opportunity2>", "<opportunity3>", "<opportunity4>"],
       "threats": ["<threat1>", "<threat2>", "<threat3>", "<threat4>"]
   }}

5. **Global Market** (Use segment-specific data):
   - "global_market": {{
       "sector": "<specific_sector_name_e.g._Seeds_Agricultural_Technology>",
       "total_market_size": {{
           "year": 2025,
           "value": "<realistic_current_market_size_based_on_sector>"
       }},
       "forecast": {{
           "year": 2030,
           "value": "<realistic_5_year_projection>",
           "cagr": <realistic_cagr_percentage>
       }},
       "growth_drivers": ["Population growth driving food demand", "Climate change adaptation needs", "Technological advancement adoption", "Sustainability regulations"],
       "major_regions": ["North America", "Europe", "Asia-Pacific", "Latin America"],
       "market_trends": ["Precision agriculture adoption", "Sustainable farming practices", "Digital transformation", "Climate-resilient crops"],
       "sustainability_initiatives": ["<initiative1>", "<initiative2>", "<initiative3>"],
       "crop_resilience_focus": ["Drought tolerance", "Disease resistance", "Climate adaptation"]
   }}

6. **Market Capture** (Include 5-year historical trend):
   - "market_capture": {{
       "current_percentage_estimated": <realistic_market_share_1_to_15_percent>,
       "confidence_level_estimated": "Medium|High",
       "historical_trend_estimated": {{
           "2020": <percentage>,
           "2021": <percentage>,
           "2022": <percentage>,
           "2023": <percentage>,
           "2024": <percentage>
       }},
       "trend_analysis": "Increasing|Stable|Declining - with brief explanation",
       "competitive_position": "Market Leader|Strong Player|Emerging Player"
   }}

**MARKET SHARE GUIDELINES:**
- No single company should have >15% market share in global agriculture
- Top 5 companies typically hold 8-15% each
- Mid-tier companies hold 3-8%
- Emerging players hold 1-5%
- Market share should show realistic trends over 5 years

REQUIREMENTS:
- Only include companies related to seeds, crop protection, agricultural biotechnology, or farm equipment
- Use 6–8 top global companies based on actual market presence and revenue
- Ensure market projections show GROWTH, not decline
- Include realistic CAGR rates (typically 4-8% for agriculture, 10-15% for agtech)
- Market capture percentages must be realistic and sum to <100% across all companies
- Historical trends should reflect actual market dynamics (consolidation, acquisitions, etc.)
- Focus on innovation leaders in sustainable agriculture and biotechnology

RESPONSE FORMAT:
Respond with **valid JSON only** using this structure:

{{
  "id": "generated-uuid-here",
  "date": "{today}",
  "competitor_data": [
    {{
      "company_name": "<company_name>",
      "profile": {{ ... }},
      "target_audience": [ ... ],
      "swot": {{ ... }},
      "global_market": {{ ... }},
      "market_capture": {{ ... }}
    }},
    {{...}}
  ]
}}

**VALIDATION CHECKLIST:**
- ✓ Market size projections show growth, not decline
- ✓ CAGR rates are realistic for the agriculture sector
- ✓ Market share percentages are realistic (<15% for any single company)
- ✓ Historical trends show logical progression
- ✓ All companies are legitimate agriculture/biotech leaders
- ✓ Data reflects current market realities as of 2025

RAW COMPANY TEXTS:
{combined_text}
"""

    try:
        logger.info("Sending prompt to OpenAI API...")  # Log the API request
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[ 
                {"role": "system", "content": "You generate valid JSON for agriculture company profiling with accurate market data. Use realistic market figures and ensure growth projections are logical. Return JSON only — no markdown, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000  # Increased to accommodate more detailed data
        )

        # Extract and clean the raw response content
        content = response.choices[0].message.content.strip()

        # Clean potential markdown wrappers
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Extract valid JSON content
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            content = content[start_idx:end_idx + 1]

        if not content or len(content) < 10:
            logger.warning("Content too short or empty after cleanup.")
            return None

        # Parse and validate the final competitor data
        parsed = json.loads(content)
        
        # Validate market data logic
        if 'competitor_data' in parsed:
            for company in parsed['competitor_data']:
                if 'global_market' in company:
                    market = company['global_market']
                    if 'total_market_size' in market and 'forecast' in market:
                        current_value = float(market['total_market_size']['value'].replace('$', '').replace('B', '').replace('T', ''))
                        forecast_value = float(market['forecast']['value'].replace('$', '').replace('B', '').replace('T', ''))
                        
                        if forecast_value <= current_value:
                            logger.warning(f"Market projection shows decline for {company['company_name']}")
                
                if 'market_capture' in company:
                    market_share = company['market_capture'].get('current_percentage', 0)
                    if market_share > 20:
                        logger.warning(f"Unrealistic market share ({market_share}%) for {company['company_name']}")

        logger.info("Enhanced competitor data generated successfully with validation.")
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.debug(f"Raw content:\n{content[:500]}")
        return None
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None
