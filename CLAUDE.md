# Claude Code — Agriculture Market Intelligence Platform

## Identity
Market intelligence engineer for an agriculture data platform.
Scrapes social media + web sources, processes data through LLMs, and serves a REST API for agricultural insights.

## Stack
- **API:** FastAPI on port 8004 (`main.py` entry point)
- **Database:** Supabase (Postgres) — all data layer in `supabase_service/`
- **LLM:** OpenAI + Langchain — processing pipeline in `llm_services/`
- **Scheduling:** APScheduler — all jobs in `skills/automation/`
- **Scraping:** Selenium + BeautifulSoup + Apify — scrapers in `scrapers/` + `utils/`
- **Containerization:** Docker (`dockerfile` + `docker-compose.yml`)

## Project Structure
```
market-intelligence/
├── main.py                    ← FastAPI entry point (imports all routes, starts schedulers)
├── skills/
│   ├── dashboards/            ← FastAPI route handlers (14 modules)
│   ├── automation/            ← APScheduler jobs (14 schedulers)
│   ├── data_infrastructure/   ← Auth, security, schemas
│   └── [other categories]
├── supabase_service/          ← Data access layer (15 service modules)
├── llm_services/              ← LLM processing (alerts, breeding, competitor, social)
├── scrapers/                  ← Web scrapers (tomato, alerts, competitor)
├── utils/                     ← Social media fetchers (LinkedIn, Facebook, Instagram, Twitter, Reddit)
├── pdf_generator/             ← Weekly/monthly PDF report generation
├── test/                      ← Test data (JSON) + test scripts
└── .claude/data/
    ├── regulations/           ← 27 country regulatory PDFs
    └── social/                ← Scraped social media data
```

## API Domains
- **Alerts** — crop/price/weather/disease alerts + detail enrichment
- **Genetics** — tomato genetic trait data
- **Patents** — agricultural patent tracking
- **Regulations** — 27-country regulatory intelligence (PDFs in `.claude/data/regulations/`)
- **Breeding** — breeding recommendations
- **Competitor** — competitor intelligence
- **Social Media** — LinkedIn, Facebook, Instagram, Twitter, Reddit content
- **Reports** — weekly + monthly PDF generation
- **Auth/Admin** — user roles (admin, editor, researcher)

## Run Commands
```bash
# Local
python main.py

# Docker
docker-compose up

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables
All in `.env` — never commit. Key vars:
- `OPENAI_API_KEY` — LLM processing
- `SUPABASE_URL` + `SUPABASE_KEY` — database
- `JWT_SECRET_KEY` — auth signing
- `SERPAPI_API_KEY` — Google search scraping
- `APIFY_API_TOKEN` — Apify scrapers
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` — Reddit API

## Rules
- Always use Haiku (`claude-haiku-4-5-20251001`) for LLM tasks where possible — right-size max_tokens
- Never commit `.env` — it contains live API keys
- Backup `.claude/data/` before modifying regulation PDFs
- Files: lowercase-kebab-case for new files
- Routes live in `skills/dashboards/`, not root `routes/` (that folder is legacy/compiled)
- Schedulers live in `skills/automation/`, not root `schedulers/` (same reason)

## Data
- **Regulations:** 27 country PDFs in `.claude/data/regulations/` (Argentina, Australia, Brazil, Canada, Chile, China, Colombia, Costa Rica, EU, GB, India, Indonesia, Iceland, Israel, Japan, Kazakhstan, Korea, Mexico, Norway, NZ, Philippines, South Africa, Turkey, Ukraine, USA, Vietnam)
- **Social:** scraped social media content in `.claude/data/social/`
- **Outputs:** example API responses in `.claude/docs/` (Alerts, Genetics, Patents, Regulations, Breeding, Competitor)

## After Changes
1. Backup `.env` and any modified service files
2. Test locally with `python main.py` before Docker build
3. Check scheduler startup in logs (`app.log`)
