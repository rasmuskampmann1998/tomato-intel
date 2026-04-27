import logging
from scrapers.tomato_id_scraper import scrape_data
from scrapers.tomato_data_scraper import scrape_details_from_id_links
from utils.genetic_data_processor import clean_and_insert_genetics

def run_genetic_scraper_pipeline():
    logging.info("Starting genetic scraper pipeline...")
    # Step 1: Scrape IDs and links
    id_link_list = scrape_data(search_term="tomato", max_pages=5)
    if not id_link_list:
        logging.error("No IDs/links scraped.")
        return
    logging.info(f"Scraped {len(id_link_list)} IDs/links.")
    # Step 2: Scrape details in memory
    details = scrape_details_from_id_links(id_link_list)
    if not details:
        logging.error("No details scraped.")
        return
    # Step 3: Insert into Supabase
    clean_and_insert_genetics(details)
    logging.info("Genetic scraper pipeline completed.") 