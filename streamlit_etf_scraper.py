import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import os
import tempfile

def scrape_etfs(url, status_placeholder):
    # Create absolute path for temporary directory
    temp_dir = os.path.join(tempfile.gettempdir(), 'webdriver')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-tools")

    try:
        # Initialize WebDriver using Selenium's built-in manager
        service = Service()
        driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
        etf_data = []
        status_placeholder.text("Loading page...")
        driver.get(url)
        time.sleep(2)
        
        # Handle cookie consent
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
            )
            cookie_button.click()
            time.sleep(1)
        except TimeoutException:
            status_placeholder.text("No cookie consent pop-up detected or already handled.")
        
        page = 1
        while True:
            status_placeholder.text(f"Processing page {page}...")
            
            # Wait for the ETF table to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#etfsTable"))
            )
            
            # Extract table rows
            rows = driver.find_elements(By.CSS_SELECTOR, "#etfsTable > tbody > tr")
            status_placeholder.text(f"Found {len(rows)} rows on page {page}.")
            
            # Extract ETF data from each row
            error_count = 0
            for row in rows:
                try:
                    name = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) > a").text
                    isin = row.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
                    if name and isin:
                        etf_data.append({"Name": name, "ISIN": isin})
                except Exception:
                    error_count += 1
            
            if error_count > 0:
                status_placeholder.text(f"Processed page {page}. Skipped {error_count} invalid rows.")
            else:
                status_placeholder.text(f"Processed page {page}.")
            
            # Attempt to navigate to the next page
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#etfsTable_next"))
                )
                if 'disabled' not in next_button.get_attribute('class'):
                    next_button.click()
                    time.sleep(2)
                    page += 1
                else:
                    status_placeholder.text("No more pages available.")
                    break
            except TimeoutException:
                status_placeholder.text("No more pages available.")
                break
    
    finally:
        try:
            driver.quit()
        except:
            pass
    
    return pd.DataFrame(etf_data)

# Streamlit UI Configuration
st.set_page_config(page_title="JustETF Scraper", page_icon="📊", layout="centered")
st.title("JustETF Scraper")
st.markdown("Enter an ETF issuer name to get their products' names and ISINs in CSV format.")

# User Input
etf_issuer = st.text_input("ETF Issuer:", "")

# Construct the URL
base_url = "https://www.justetf.com/it/search.html"
url = f"{base_url}?query={etf_issuer}&search=ETFS"

# Scrape Button
if st.button("Get ETF Data"):
    if not etf_issuer:
        st.error("Please enter an ETF issuer name.")
    else:
        status = st.empty()
        try:
            with st.spinner('Scraping data...'):
                df = scrape_etfs(url, status)
            st.success(f"Found {len(df)} ETFs!")
            st.dataframe(df)
            
            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{etf_issuer}_etfs.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Instructions
st.markdown("""
---
### How to Use:
1. Enter an ETF issuer name (e.g., iShares, Vanguard, SPDR, etc.)
2. Click "Get ETF Data"
3. Download the CSV file with the results
""")
