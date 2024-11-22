import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time

def scrape_etfs(url, status_placeholder):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode.
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.binary_location = "/usr/bin/chromium-browser"  # Path to Chromium

    # Initialize WebDriver using webdriver_manager.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    etf_data = []
    try:
        status_placeholder.text("Loading page...")
        driver.get(url)
        time.sleep(2)  # Allow time for the page to load.
        
        # Handle cookie consent.
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
            
            # Wait for the ETF table to load.
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#etfsTable"))
            )
            
            # Extract table rows.
            rows = driver.find_elements(By.CSS_SELECTOR, "#etfsTable > tbody > tr")
            status_placeholder.text(f"Found {len(rows)} rows on page {page}.")
            
            # Extract ETF data from each row.
            for row in rows:
                try:
                    name = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) > a").text
                    isin = row.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
                    if name and isin:
                        etf_data.append({"Name": name, "ISIN": isin})
                except Exception as e:
                    st.write(f"Error processing row: {e}")
            
            # Attempt to navigate to the next page.
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
        driver.quit()
    
    return pd.DataFrame(etf_data)

# Streamlit UI Configuration
st.set_page_config(page_title="JustETF Scraper", page_icon="📊", layout="centered")
st.title("JustETF Scraper")
st.markdown("Enter a URL from JustETF to get ETF data in CSV format.")

# User Input
url = st.text_input("JustETF URL:", "https://www.justetf.com/en/search.html?query=...")

# Scrape Button
if st.button("Get ETF Data"):
    if not url.startswith("https://www.justetf.com/"):
        st.error("Please enter a valid JustETF URL.")
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
                file_name="etfs.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Instructions
st.markdown("""
---
### How to Use:
1. Go to [JustETF](https://www.justetf.com/)
2. Search for the ETFs you're interested in.
3. Copy the URL from your browser.
4. Paste the URL above and click "Get ETF Data".
5. Download the CSV file.
""")
