import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time

st.set_page_config(
    page_title="ETF Scraper",
    page_icon="📊",
    layout="centered"
)

st.title("JustETF Scraper")
st.markdown("""
Enter a URL from JustETF to get ETF data in CSV format.
""")

# Setup Chrome options at the start
@st.cache_resource
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_etfs(url, status_placeholder):
    driver = get_chrome_driver()
    etf_data = []
    
    try:
        status_placeholder.write("Loading page...")
        driver.get(url)
        time.sleep(2)
        
        # Handle cookie consent
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
            )
            cookie_button.click()
            time.sleep(1)
        except:
            status_placeholder.write("Cookie consent handled")
        
        page = 1
        while True:
            status_placeholder.write(f"Processing page {page}")
            
            # Wait for table
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#etfsTable"))
            )
            
            # Get rows
            rows = driver.find_elements(By.CSS_SELECTOR, "#etfsTable > tbody > tr")
            
            # Process rows
            for row in rows:
                try:
                    name = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) > a").text
                    isin = row.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
                    if name and isin:
                        etf_data.append({"Name": name, "ISIN": isin})
                except Exception as e:
                    continue
            
            # Try next page
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#etfsTable_next"))
                )
                if 'disabled' not in next_button.get_attribute('class'):
                    next_button.click()
                    time.sleep(2)
                    page += 1
                else:
                    break
            except TimeoutException:
                break
        
        return pd.DataFrame(etf_data)
    
    finally:
        driver.quit()

# URL input
url = st.text_input("Enter JustETF URL:", placeholder="https://www.justetf.com/en/search.html?query=...")

if st.button("Get ETF Data", type="primary"):
    if not url.startswith("https://www.justetf.com/"):
        st.error("Please enter a valid JustETF URL")
    else:
        status = st.empty()
        progress_bar = st.progress(0)
        
        try:
            with st.spinner('Scraping data...'):
                df = scrape_etfs(url, status)
            
            st.success(f"Found {len(df)} ETFs!")
            
            # Show preview
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="etfs.csv",
                mime="text/csv",
            )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

st.markdown("""
---
### How to use:
1. Go to [JustETF](https://www.justetf.com/)
2. Search for the ETFs you want
3. Copy the URL from your browser
4. Paste it here and click "Get ETF Data"
5. Download the CSV file
""")

