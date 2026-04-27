import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def scrape_data(search_term="tomato", max_pages=5):
    driver = None
    try:
        logging.info("Initializing Chrome WebDriver...")
        driver = setup_chrome_driver()
        url = "https://npgsweb.ars-grin.gov/gringlobal/search"
        logging.info(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(3)
        search_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='MainContent_txtSearch']"))
        )
        search_input.clear()
        search_input.send_keys(search_term)
        search_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='MainContent_btnSimple']"))
        )
        search_button.click()
        time.sleep(10)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        all_data = []
        def scrape_current_page(page_num):
            logging.info(f"Scraping data from page {page_num}...")
            results_table = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, "//table[@class='accessions stripe row-border responsive no-wrap dataTable no-footer dtr-inline dt-checkboxes-select']"))
            )
            tbody = results_table.find_element(By.TAG_NAME, "tbody")
            page_data = []
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            logging.info(f"Page {page_num}: Found {len(rows)} rows")
            for i, row in enumerate(rows, 1):
                try:
                    all_a_elements = row.find_elements(By.TAG_NAME, "a")
                    if all_a_elements:
                        for a_element in all_a_elements:
                            id_text = a_element.text.strip()
                            link = a_element.get_attribute("href")
                            if id_text and link and id_text.startswith("PI"):
                                entry = {
                                    "id": id_text,
                                    "link": link,
                                    "page": page_num,
                                    "scraped_at": datetime.now().isoformat()
                                }
                                page_data.append(entry)
                                logging.info(f"Page {page_num}, Row {i}: ID = {id_text}")
                                break
                except Exception as e:
                    logging.warning(f"Page {page_num}, Row {i}: Could not extract data - {str(e)}")
                    continue
            all_data.extend(page_data)
            return page_data
        scrape_current_page(1)
        try:
            main_content = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='MainContent_ctrlQueryResults_AccSearchresults']"))
            )
            searchtable_wrapper = main_content.find_element(By.XPATH, ".//div[@id='searchtable_wrapper']")
            pagination_div = searchtable_wrapper.find_element(By.XPATH, ".//div[@id='searchtable_paginate']")
            pagination_links = pagination_div.find_elements(By.XPATH, ".//a[contains(@class,'paginate_button') and not(contains(@class,'previous')) and not(contains(@class,'next'))]")
            available_pages = []
            for link in pagination_links:
                page_text = link.text.strip()
                if page_text.isdigit():
                    available_pages.append(int(page_text))
            available_pages = sorted(available_pages)
            pages_to_scrape = available_pages[:max_pages]
            for page_num in pages_to_scrape[1:]:
                try:
                    page_link = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@id='searchtable_paginate']//a[contains(@class,'paginate_button') and normalize-space()='{page_num}']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView();", page_link)
                    time.sleep(2)
                    page_link.click()
                    time.sleep(5)
                    scrape_current_page(page_num)
                except Exception as e:
                    logging.error(f"Error navigating to page {page_num}: {str(e)}")
                    continue
        except Exception as e:
            logging.warning(f"Could not find pagination or error in pagination: {str(e)}")
            logging.info("Continuing with data from first page only...")
        logging.info(f"Total data collected: {len(all_data)} entries across all pages")
        return all_data
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return None
    finally:
        if driver:
            logging.info("Closing browser...")
            driver.quit() 