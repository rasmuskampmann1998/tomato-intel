import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def safe_extract_text(driver, xpath, element_name):
    try:
        element = driver.find_element(By.XPATH, xpath)
        text = element.text.strip()
        logger.info(f"Extracted {element_name}: {text}")
        return text
    except NoSuchElementException:
        logger.warning(f"Element not found for {element_name} with XPath: {xpath}")
        return ""

def clean_origin(origin_text):
    if not origin_text:
        return ""
    origin_text = origin_text.replace("Developed – ", "").replace("Collected – ", "")
    if "," in origin_text:
        parts = origin_text.split(",")
        return parts[-1].strip()
    return origin_text

def scrape_plant_data(driver, url, plant_id):
    logger.info(f"Starting to scrape REAL TIME data for {plant_id} from {url}")
    try:
        driver.get(url)
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='container body-content']"))
        )
        logger.info(f"Page loaded successfully for {plant_id}")
        variety_name = safe_extract_text(driver, "//span[@id='MainContent_ctrlSum_lblTopName']", "Variety Name")
        origin_raw = safe_extract_text(driver, "//span[@id='MainContent_ctrlSum_lblOrigin']", "Origin")
        country_of_origin = clean_origin(origin_raw)
        genus = safe_extract_text(driver, "//span[@id='MainContent_ctrlSum_lblTaxon']//a[1]", "Genus")
        collection_date = safe_extract_text(driver, "//span[@id='MainContent_ctrlSum_lblReceived']", "Collection Date")
        data = {
            "variety_name": variety_name,
            "country_of_origin": country_of_origin,
            "genus": genus,
            "crop_name": "tomato",
            "collection_date": collection_date
        }
        logger.info(f"Successfully scraped REAL TIME data for {plant_id}:")
        logger.info(f"  Variety Name: {variety_name}")
        logger.info(f"  Country of Origin: {country_of_origin}")
        logger.info(f"  Genus: {genus}")
        logger.info(f"  Collection Date: {collection_date}")
        return data
    except TimeoutException:
        logger.error(f"Timeout waiting for page to load for {plant_id}")
        return None
    except Exception as e:
        logger.error(f"Error scraping data for {plant_id}: {str(e)}")
        return None

def scrape_details_from_id_links(id_link_list):
    logger.info("Starting in-memory tomato detail scraping for all IDs/links...")
    driver = setup_driver()
    all_plant_data = []
    for i, plant in enumerate(id_link_list, 1):
        plant_id = plant['id']
        plant_url = plant['link']
        logger.info(f"Processing plant {i}/{len(id_link_list)}: {plant_id}")
        plant_data = scrape_plant_data(driver, plant_url, plant_id)
        if plant_data:
            # Remove 'id' if present (modular)
            if "id" in plant_data:
                del plant_data["id"]
            all_plant_data.append(plant_data)
            logger.info(f"Successfully processed {plant_id}")
        else:
            logger.error(f"Failed to process {plant_id}")
        time.sleep(2)
    driver.quit()
    logger.info(f"Completed scraping details for {len(all_plant_data)} plants.")
    # Robust: Remove 'id' from all records before returning
    for record in all_plant_data:
        if "id" in record:
            del record["id"]
    return all_plant_data 