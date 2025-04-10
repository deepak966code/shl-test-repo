import argparse
import csv
import os
import time
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.service import Service
# ✅ Extract test duration & description from detail page
def extract_details_from_page(driver, link):
    duration = ""
    description = ""
    try:
        driver.get(link)
        time.sleep(1.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
       
        # Duration
        duration_para = soup.find('p', string=lambda t: t and 'Completion Time' in t)
        if duration_para:
            duration = ''.join(filter(str.isdigit, duration_para.text))

        # Description
        desc_header = soup.find('h4', string='Description')
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            if desc_p:
                description = desc_p.get_text(separator=" ", strip=True)
        

    except Exception as e:
        print(f"⚠️ Failed to extract details from {link}: {e}")

    return duration, description

# ✅ Parse CLI arguments
parser = argparse.ArgumentParser(description="SHL Crawler - Keyword Search with Details (Selenium)")
parser.add_argument("keywords", nargs="+", help="List of keywords to search (e.g., manager engineer analyst)")
args = parser.parse_args()

# ✅ Ensure output directory exists
os.makedirs("data", exist_ok=True)

chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium"
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")


chrome_service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
detail_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)


wait = WebDriverWait(driver, 10)

all_jobs = []

for keyword in args.keywords:
    print(f"🔍 Searching for: {keyword}")
    driver.get("https://www.shl.com/solutions/products/product-catalog/")

    try:
        # Wait for and enter keyword
        search_input = wait.until(EC.presence_of_element_located((By.NAME, "keyword")))
        search_input.clear()
        search_input.send_keys(keyword)

        # Wait for and click search
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "Form_FilteringFormKeywords_action_doFilteringForm")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", search_button)

        # Wait for results
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.js-target-table-wrapper table tbody tr")))
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            title_el = cells[0].find_element(By.TAG_NAME, "a") if cells else None
            title = title_el.text.strip() if title_el else ''
            link = title_el.get_attribute("href") if title_el else ''

            remote = 'Yes' if len(cells) > 1 and cells[1].find_elements(By.CSS_SELECTOR, "span.catalogue__circle.-yes") else 'No'
            adaptive = 'Yes' if len(cells) > 2 and cells[2].find_elements(By.CSS_SELECTOR, "span.catalogue__circle.-yes") else 'No'

            key_spans = row.find_elements(By.CSS_SELECTOR, "span.product-catalogue__key")
            keys = ', '.join([span.text.strip() for span in key_spans])

            # 🆕 Extract duration and description from detail page
            duration, description = extract_details_from_page(detail_driver, link)

            all_jobs.append({
                'Job Title': title,
                'Link': link,
                'Remote Testing': remote,
                'Adaptive/IRT': adaptive,
                'Test Type': keys,
                'Duration': duration,
                'Description': duration + description
            })

    except Exception as e:
        print(f"⚠️ Error retrieving data for keyword '{keyword}': {str(e)}")
        traceback.print_exc()

# ✅ Clean up
driver.quit()
detail_driver.quit()

# ✅ Write results to file
output_file = "data/first.csv"
if all_jobs:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Job Title', 'Link', 'Remote Testing', 'Adaptive/IRT', 'Test Type', 'Duration', 'Description'
        ])
        writer.writeheader()
        writer.writerows(all_jobs)
    print(f"✅ Saved {len(all_jobs)} results to {output_file}")
else:
    print("❌ No results found.")
