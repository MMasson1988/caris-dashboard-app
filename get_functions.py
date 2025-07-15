import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Charger les identifiants
load_dotenv('id_cc.env')
email = os.getenv('EMAIL')
password_cc = os.getenv('PASSWORD')

# Configurer le navigateur
options = Options()
options.add_argument("start-maximized")
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

wait = WebDriverWait(driver, 120)

# Fonction de connexion
def commcare_login():
    driver.get(
        'https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/3eb9f92d8d82501ebe5c8cb89b83dbba/'
    )
    wait.until(EC.presence_of_element_located((By.ID, "id_auth-username"))).send_keys(email)
    driver.find_element(By.ID, "id_auth-password").send_keys(password_cc)
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()

# Connexion
commcare_login()

# Cliquer sur "Prepare export"
prepare_btn_xpath = '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'
wait.until(EC.element_to_be_clickable((By.XPATH, prepare_btn_xpath))).click()

# Attendre que le lien de téléchargement apparaisse
download_link_xpath = '//*[@id="download-progress"]//form/a'
download_link = wait.until(EC.element_to_be_clickable((By.XPATH, download_link_xpath)))
download_link.click()
time.sleep(30)

driver.quit()
#=========================================================================================================================================================================
