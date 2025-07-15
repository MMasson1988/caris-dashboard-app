import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Fonction générique pour lancer un export depuis une URL CommCare
def download_commcare_export(export_url, email, password):
    try:
        options = Options()
        options.add_argument("start-maximized")
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        wait = WebDriverWait(driver, 120)

        # Accéder à la page d'exportation et se connecter
        driver.get(export_url)
        wait.until(EC.presence_of_element_located((By.ID, "id_auth-username"))).send_keys(email)
        driver.find_element(By.ID, "id_auth-password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()

        # Cliquer sur "Prepare export"
        prepare_btn_xpath = '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'
        wait.until(EC.element_to_be_clickable((By.XPATH, prepare_btn_xpath))).click()

        # Attendre et cliquer sur le lien de téléchargement
        download_link_xpath = '//*[@id="download-progress"]//form/a'
        download_link = wait.until(EC.element_to_be_clickable((By.XPATH, download_link_xpath)))
        download_link.click()

        time.sleep(30)  # Attendre le téléchargement
        print(f"✅ Téléchargement depuis {export_url[:60]}... réussi.")
        driver.quit()

    except Exception as e:
        print(f"❌ Erreur avec {export_url[:60]}... : {e}")
        try:
            driver.quit()
        except:
            pass

# Fonction principale
def get_commcare_case():
    load_dotenv('id_cc.env')
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    # Liste des URL d’exports CommCare
    export_urls = [
        # Case export
        'https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/3eb9f92d8d82501ebe5c8cb89b83dbba/',
        # Form export - is_accept_form
        'https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/269567f0b84da5a1767712e519ced62e/',
        # Form export - hh_0
        'https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/9b22af972e065eda11f311ac0a1586e5/'
    ]

    for url in export_urls:
        download_commcare_export(url, email, password)

# Exécution
if __name__ == "__main__":
    get_commcare_case()
