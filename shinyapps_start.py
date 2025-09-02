import time, sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EMAIL = "mbenjudas@gmail.com"
PASSWORD = "mirlande_1988"
TARGET_URL = "https://www.shinyapps.io/admin/#/application/15137338"
LOGIN_URL = (
    "https://login.shinyapps.io/login"
    "?redirect=%2Foauth%2Fauthorize%3Fclient_id%3Drstudio-shinyapps"
    "%26redirect_uri%3Dhttps%253A%252F%252Fwww.shinyapps.io%252Fauth%252Foauth%252Ftoken"
    "%26response_type%3Dcode%26scopes%3D%252A%26show_auth%3D0"
    "%26state%3DeyJyZWRpcmVjdCI6ICIvYXBwbGljYXRpb24vMTUxMzczMzgifQ%253D%253D"
)
TIMEOUT_PAGE = 60
WAIT_FOR_START_SECS = 600

def driver_start():
    opts = Options()
    opts.add_argument("--window-size=1400,950")
    return webdriver.Chrome(options=opts)

def ready(d): return d.execute_script("return document.readyState") == "complete"

def find_first(drv, locs, timeout=TIMEOUT_PAGE, cond="clickable"):
    for by, sel in locs:
        try:
            if cond == "present":
                return WebDriverWait(drv, timeout).until(EC.presence_of_element_located((by, sel)))
            if cond == "visible":
                return WebDriverWait(drv, timeout).until(EC.visibility_of_element_located((by, sel)))
            return WebDriverWait(drv, timeout).until(EC.element_to_be_clickable((by, sel)))
        except Exception:
            continue
    raise TimeoutError(f"no element found via {locs}")

def login(drv):
    drv.get(LOGIN_URL)
    WebDriverWait(drv, TIMEOUT_PAGE).until(ready)
    email = find_first(drv, [
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.XPATH, "//input[@placeholder='Email' or contains(@id,'email')]")
    ], cond="visible")
    email.clear(); email.send_keys(EMAIL)
    find_first(drv, [
        (By.XPATH, "//button[normalize-space()='Continue']"),
        (By.CSS_SELECTOR, "button[type='submit']")
    ]).click()
    pwd = find_first(drv, [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.XPATH, "//input[@placeholder='Password' or contains(@id,'password')]")
    ], cond="visible")
    pwd.clear(); pwd.send_keys(PASSWORD)
    find_first(drv, [
        (By.XPATH, "//button[normalize-space()='Log In' or normalize-space()='Log in']"),
        (By.CSS_SELECTOR, "button[type='submit']")
    ]).click()
    WebDriverWait(drv, TIMEOUT_PAGE).until(lambda d: "authorize" not in d.current_url)

def open_target_page(drv):
    drv.get(TARGET_URL)
    time.sleep(2)
    # If on the Recent Applications page, click the 'dashboard-pvvih' link in the Name column
    try:
        dashboard_link = WebDriverWait(drv, 5).until(
            EC.presence_of_element_located((By.XPATH, "//table//a[contains(text(),'dashboard-pvvih')]"))
        )
        if dashboard_link.is_displayed() and dashboard_link.is_enabled():
            print("Found 'dashboard-pvvih' link, attempting to click...")
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", dashboard_link)
            time.sleep(0.5)
            dashboard_link.click()
            print("Clicked 'dashboard-pvvih' link in Recent Applications.")
            time.sleep(2)
        else:
            print("'dashboard-pvvih' link found but not clickable (not displayed or not enabled).")
    except Exception as e:
        print("No 'dashboard-pvvih' link found or not clickable:", e)
    find_first(drv, [
        (By.XPATH, "//*[normalize-space()='INSTANCES']"),
        (By.XPATH, "//*[contains(., 'APPLICATION USAGE')]")
    ], cond="visible")

def get_instances_panel(drv):
    return find_first(drv, [
        (By.XPATH, "//*[normalize-space()='INSTANCES']"
                   "/ancestor::*[contains(@class,'panel') or contains(@class,'card')][1]")
    ], cond="present")

def instance_running(panel):
    try:
        panel.find_element(By.XPATH,
            ".//button[.//i[contains(@class,'ti-control-pause') or contains(@class,'fa-pause') or contains(@class,'glyphicon-pause')]]"
        )
        return True
    except Exception:
        try:
            panel.find_element(By.XPATH, ".//button[contains(@title,'Stop') or contains(@uib-tooltip,'Stop')]")
            return True
        except Exception:
            return False

def wait_and_click_start(drv):
    panel = get_instances_panel(drv)
    if instance_running(panel):
        print("Instance already running. No Start click.")
        return
    def start_button_present(_):
        # 1. Try button with ti-control-play icon
        try:
            btn = panel.find_element(
                By.XPATH,
                ".//button[.//i[contains(@class,'ti-control-play')]]"
            )
            if btn.is_displayed() and btn.is_enabled():
                print("Found Start button with ti-control-play icon.")
                return btn
        except Exception:
            pass
        # 2. Try element with [title='Start']
        try:
            btn = panel.find_element(
                By.XPATH,
                ".//*[@title='Start' and (self::button or self::a)]"
            )
            if btn.is_displayed() and btn.is_enabled():
                print("Found Start button with [title='Start'].")
                return btn
        except Exception:
            pass
        return False
    print(f"Waiting for Start button (up to {WAIT_FOR_START_SECS}s)...")
    btn = WebDriverWait(drv, WAIT_FOR_START_SECS).until(start_button_present)
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.2)
    try:
        btn.click()
        print("Clicked Start button.")
    except Exception:
        drv.execute_script("arguments[0].click();", btn)
        print("Clicked Start button with JS.")
    # Wait for Pause/Stop to confirm
    print("Waiting for Pause/Stop button to confirm instance is running...")
    WebDriverWait(drv, 120).until(lambda d: (
        panel.find_elements(By.XPATH, ".//button[.//i[contains(@class,'ti-control-pause') or contains(@class,'fa-pause') or contains(@class,'glyphicon-pause')]]")
        or panel.find_elements(By.XPATH, ".//button[contains(@title,'Stop') or contains(@uib-tooltip,'Stop')]")))
    print("Pause/Stop button is now visible. Instance is running.")

def main():
    drv = driver_start()
    try:
        login(drv)
        open_target_page(drv)
        wait_and_click_start(drv)
    except Exception as e:
        print("ERROR:", e)
        try: drv.save_screenshot("start_when_appears_error.png")
        except: pass
        sys.exit(1)
    finally:
        time.sleep(1.0)
        drv.quit()

if __name__ == "__main__":
    main()
