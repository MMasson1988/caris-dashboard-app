#Importing packages

import pandas as pd
import numpy as np
from datetime import datetime
import pymysql
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from dotenv import load_dotenv

#Connecting to Commcare
load_dotenv('id_cc.env')
email = os.getenv('EMAIL')
password_cc = os.getenv('PASSWORD')

# Set download directory
download_dir = os.path.join(os.getcwd(), "downloads")
os.makedirs(download_dir, exist_ok=True)

#Defining the driver with download preferences
options = Options()
options.add_argument("--start-maximized")
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)
wait = WebDriverWait(driver, 30)

def login_to_commcare():
    """Login to CommCare once and reuse session"""
    try:
        driver.find_element(By.XPATH, '//*[@id="id_auth-username"]').send_keys(email)
        driver.find_element(By.XPATH, '//*[@id="id_auth-password"]').send_keys(password_cc)
        driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
        # Wait for login to complete
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        print("Successfully logged in to CommCare")
    except Exception as e:
        print(f"Login failed: {e}")

def download_file(download_name):
    """Generic function to download files from CommCare"""
    try:
        # Click download button
        download_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button/span[1]')))
        download_btn.click()
        print(f"Initiated download for {download_name}")
        
        # Wait for download to be ready and click download link
        download_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download-progress"]/div/div/div[2]/div[1]/form/a/span[1]')))
        download_link.click()
        print(f"Download started for {download_name}")
        
        # Wait for download to complete
        time.sleep(10)
        print(f"Download completed for {download_name}")
        
    except Exception as e:
        print(f"Download failed for {download_name}: {e}")

def commcare_household():
    """Download household count data"""
    try:
        driver.get('https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/091321e0524e3ae7f5d5c1d3f43dccca/')
        
        # Login if not already logged in
        if "login" in driver.current_url.lower():
            login_to_commcare()
        
        download_file("Household count")
        
    except Exception as e:
        print(f"Error in commcare_household: {e}")

def commcare_all_gardens():
    """Download all gardens data"""
    try:
        driver.get('https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/789629a97bddd10b4648d5138d17908e/')
        
        download_file("All gardens")
        
    except Exception as e:
        print(f"Error in commcare_all_gardens: {e}")

def main():
    """Main function to orchestrate downloads"""
    try:
        print("Starting CommCare data downloads...")
        
        # Download household data
        commcare_household()
        
        # Download gardens data
        commcare_all_gardens()
        
        print("All downloads completed!")
        print(f"Files saved to: {download_dir}")
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()