# login_shinyapps.py
# -*- coding: utf-8 -*-
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL = ("https://login.shinyapps.io/login?redirect=%2Foauth%2Fauthorize%3Fclient_id%3Drstudio-shinyapps"
             "%26redirect_uri%3Dhttps%253A%252F%252Fwww.shinyapps.io%252Fauth%252Foauth%252Ftoken%26response_type%3Dcode"
             "%26scopes%3D%252A%26show_auth%3D0%26state%3DeyJyZWRpcmVjdCI6ICIvYXBwbGljYXRpb24vMTUxMzczMzgifQ%253D%253D")

EMAIL = "mbenjudas@gmail.com"
PASSWORD = "mirlande_1988"

TIMEOUT = 45

def start_driver(headless=False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-dev-shm-usage")
    # modern Selenium auto-manages ChromeDriver
    return webdriver.Chrome(options=opts)

def wait_ready(driver, timeout=TIMEOUT):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def find_first(driver, locators, timeout=TIMEOUT, condition="clickable"):
    for by, sel in locators:
        try:
            if condition == "present":
                return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, sel)))
            elif condition == "visible":
                return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, sel)))
            else:
                return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
        except Exception:
            continue
    raise TimeoutError(f"Element not found with any locator: {locators}")

def click_cookie_banner_if_any(driver):
    candidates = [
        (By.ID, "onetrust-accept-btn-handler"),
        (By.XPATH, "//button[contains(translate(., 'ACEPTALLCOOKIES', 'aceptallcookies'), 'accept')]"),
        (By.XPATH, "//button[contains(., 'Accept All')]"),
    ]
    try:
        btn = find_first(driver, candidates, timeout=5)
        btn.click()
        time.sleep(0.5)
    except Exception:
        pass

def main():
    driver = start_driver(headless=False)
    try:
        driver.get(LOGIN_URL)
        wait_ready(driver)
        click_cookie_banner_if_any(driver)

        # --- Step 1: Email ---
        email_locators = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.XPATH, "//input[@placeholder='Email' or @aria-label='Email' or contains(@id,'email')]"),
        ]
        email_input = find_first(driver, email_locators, condition="visible")
        email_input.clear()
        email_input.send_keys(EMAIL)

        # Continue button (several possibilities)
        continue_locators = [
            (By.XPATH, "//button[normalize-space()='Continue']"),
            (By.XPATH, "//button[.//span[normalize-space()='Continue']]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Continue')]"),
        ]
        cont_btn = find_first(driver, continue_locators)
        cont_btn.click()

        # Sometimes ENTER works better:
        # email_input.send_keys(Keys.RETURN)

        # --- Step 2: Password (wait for transition) ---
        password_locators = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@placeholder='Password' or @aria-label='Password' or contains(@id,'password')]"),
        ]
        pwd_input = find_first(driver, password_locators, condition="visible")
        pwd_input.clear()
        pwd_input.send_keys(PASSWORD)

        # Log In button
        login_locators = [
            (By.XPATH, "//button[normalize-space()='Log In']"),
            (By.XPATH, "//button[normalize-space()='Log in']"),
            (By.XPATH, "//button[contains(., 'Log In') or contains(., 'Log in')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]
        login_btn = find_first(driver, login_locators)
        login_btn.click()

        # --- Step 3: Wait for redirect / success ---
        # Expect to be redirected to shinyapps OAuth target or an app/dashboard.
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: "token" in d.current_url
            or "authorize" not in d.current_url  # moved off the login page
        )

        print("[OK] Login flow completed. Current URL:", driver.current_url)

    except Exception as e:
        print("[ERROR] Login failed:", e)
        # Optional: capture a screenshot for debugging
        try:
            driver.save_screenshot("login_error.png")
            print("Saved screenshot to login_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        # Keep the browser open a bit (debug). Set to 0 to close immediately.
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
