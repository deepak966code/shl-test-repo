import argparse
import csv
import os
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# 🔽 Dropdown selector for Choices.js
def select_dropdown(driver, wait, holder_id, option_text):
    print(f"➡️ Selecting {option_text} for {holder_id}")
    if not option_text:
        print(f"⚠️ Skipping {holder_id} as no value provided")
        return
    try:
        container = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#{holder_id} .choices")))
        container.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"#{holder_id} .choices__list--dropdown")))
        options = driver.find_elements(By.CSS_SELECTOR, f"#{holder_id} .choices__item--selectable")
        for option in options:
            if option.text.strip().lower() == option_text.strip().lower():
                option.click()
                print(f"✅ Selected {option_text} in {holder_id}")
                break
        else:
            print(f"❌ Option '{option_text}' not found in {holder_id}")
    except Exception as e:
        print(f"⚠️ Dropdown error in '{holder_id}': {e}")

# 🧪 Extract additional details from test page
def extract_details_from_page(driver, link):
    duration = ""
    description = ""
    try:
        print(f"🔗 Opening detail page: {link}")
        driver.get(link)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1.5)  # Give some time for JS to render content

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Duration
        duration_para = soup.find('p', string=lambda t: t and 'Completion Time' in t)
        if duration_para:
            duration = ''.join(filter(str.isdigit, duration_para.text))
            print(f"⏱ Duration found: {duration}")
        else:
            print("❌ Duration not found")

        # Description
        desc_header = soup.find('h4', string='Description')
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            if desc_p:
                description = desc_p.get_text(separator=" ", strip=True)
                print(f"📝 Description found")
            else:
                print("❌ Description paragraph not found")
        else:
            print("❌ Description header not found")

    except Exception as e:
        print(f"⚠️ Failed to extract details from {link}: {e}")
    return duration, description


def main():
    try:
        parser = argparse.ArgumentParser(description="SHL Catalog Scraper with Filters (Selenium)")
        parser.add_argument("--job_family", help="Job Family filter (e.g. Safety)")
        parser.add_argument("--job_level", help="Job Level filter")
        parser.add_argument("--industry", help="Industry filter")
        parser.add_argument("--language", help="Language filter")
        parser.add_argument("--output", default="data/second.csv", help="CSV file path to save results")
        args = parser.parse_args()

        print(f"🟢 Running second.py with arguments:")
        print(vars(args))

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        jobs = []

       # Set path to chromedriver
        chrome_driver_path = "C:/path/to/chromedriver.exe"
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("start-maximized")  # open Browser in maximized mode
        chrome_options.add_argument("disable-infobars")  # disabling infobars
        chrome_options.add_argument("--disable-extensions")  # disabling extensions
        chrome_options.add_argument("--disable-gpu")  # applicable to windows OS only
        chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        
        # Create Service object for chromedriver
        chrome_service = Service(chrome_driver_path)
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        # Open URL
        driver.get("https://google.com")
        
        # If you need another driver with the same configuration:
        detail_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        wait = WebDriverWait(driver, 10)

        driver.get("https://www.shl.com/solutions/products/product-catalog/")

        # 🎯 Apply filters
        select_dropdown(driver, wait, "Form_FilteringForm_job_family_Holder", args.job_family)
        select_dropdown(driver, wait, "Form_FilteringForm_job_level_Holder", args.job_level)
        select_dropdown(driver, wait, "Form_FilteringForm_industry_Holder", args.industry)
        select_dropdown(driver, wait, "Form_FilteringForm_language_Holder", args.language)

        print("🔍 Applying filters and scraping data...")
        search_btn = driver.find_element(By.ID, "Form_FilteringForm_action_doFilteringForm")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(2)

        while True:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.js-target-table-wrapper table tbody tr")))
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            print(f"📄 Found {len(rows)} rows on this page")

            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    title_el = cells[0].find_element(By.TAG_NAME, "a") if cells else None
                    title = title_el.text.strip() if title_el else ''
                    link = title_el.get_attribute("href") if title_el else ''
                except Exception as e:
                    print(f"⚠️ Row parsing error: {e}")
                    title, link = '', ''

                remote = 'Yes' if len(cells) > 1 and cells[1].find_elements(By.CSS_SELECTOR, 'span.catalogue__circle.-yes') else 'No'
                adaptive = 'Yes' if len(cells) > 2 and cells[2].find_elements(By.CSS_SELECTOR, 'span.catalogue__circle.-yes') else 'No'
                key_spans = row.find_elements(By.CSS_SELECTOR, 'span.product-catalogue__key')
                keys = ', '.join([span.text.strip() for span in key_spans])

                # 🆕 Extract details from detail page
                duration, description = extract_details_from_page(detail_driver, link)

                jobs.append({
                    'Job Title': title,
                    'Link': link,
                    'Remote Testing': remote,
                    'Adaptive/IRT': adaptive,
                    'Test Type': keys,
                    'Duration': duration,
                    'Description': description
                })

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "li.-arrow.-next a.pagination__arrow")
                next_href = next_btn.get_attribute("href")
                if next_href:
                    next_url = "https://www.shl.com" + next_href
                    print(f"➡️ Next page: {next_url}")
                    driver.get(next_url)
                    time.sleep(2)
                else:
                    break
            except:
                print("✅ Last page reached.")
                break

        driver.quit()
        detail_driver.quit()

        # 💾 Save to CSV
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Job Title', 'Link', 'Remote Testing', 'Adaptive/IRT', 'Test Type', 'Duration', 'Description'
            ])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"✅ Done. {len(jobs)} results saved to {args.output}")

    except Exception as e:
        print("❌ An unexpected error occurred in second.py:")
        print(e)
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
