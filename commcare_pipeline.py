# coding: utf-8
# Description :
#  Script d’automatisation pour se connecter à CommCare, lancer les exports personnalisés
#  et télécharger les fichiers. Inclut des options Chrome visant à réduire les avertissements
#  liés à TensorFlow Lite et au délégué XNNPACK (Live Caption, etc.).

import os
import time
import warnings
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Empêcher TensorFlow d’émettre des messages de log (niveau INFO/WARNING)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Charger les identifiants CommCare depuis les fichiers .env
load_dotenv("dot.env")
load_dotenv("id_cc.env")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Configuration de Chrome avec des options pour réduire les logs et désactiver certaines fonctionnalités ML
def build_chrome_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    # Réduire le niveau de log général
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    # Désactiver les fonctionnalités ML de Chrome responsables des messages XNNPACK
    options.add_argument("--disable-features=LiveCaption,UseMLSpeechRecognition")
    # Ne pas lancer le profil utilisateur habituel (réduit les risques de corruption)
    # options.add_argument("--user-data-dir=/tmp/chrome-profile")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

# Liste des exports CommCare à télécharger
DOWNLOAD_LINKS = [
    {
        "name": "Household Mother",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/3eb9f92d8d82501ebe5c8cb89b83dbba/"
    },
    {
        "name": "Ajout de menage",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/269567f0b84da5a1767712e519ced62e/"
    },
    {
        "name": "Appel PTME (Nouveau)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/9b22af972e065eda11f311ac0a1586e5/"
    },
    {
        "name": "CaseID",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/af6c4186011182dfda68a84536231f68/"
    },
    {
        "name": "Household muso",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/462626788779f3781f9b9ebcce2b1a37/"
    },
    {
        "name": "Muso group",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/462626788779f3781f9b9ebcce200225/"
    },
    {
        "name": "Muso ppi",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/f5daab6b0cc722a5db175e9ad86d8cda/"
    },
    {
        "name": "All Garden",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/789629a97bddd10b4648d5138d17908e/"
    }
]

# Connexion à CommCare
def login_to_commcare(driver: webdriver.Chrome) -> None:
    print("🔐 Connexion à CommCare…")
    # On utilise l’URL du premier lien pour déclencher la connexion
    driver.get(DOWNLOAD_LINKS[0]["url"])
    try:
        username_field = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "id_auth-username"))
        )
        username_field.clear()
        username_field.send_keys(EMAIL)

        password_field = driver.find_element(By.ID, "id_auth-password")
        password_field.clear()
        password_field.send_keys(PASSWORD)

        # Essayons plusieurs sélecteurs pour trouver le bouton « Se connecter »
        selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            '.btn-primary',
            '[name="submit"]',
            'button.btn'
        ]

        button = None
        for selector in selectors:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except Exception:
                continue

        if button:
            # Clic sur le bouton
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            try:
                button.click()
            except Exception:
                driver.execute_script("arguments[0].click();", button)
            print("✅ Connexion réussie.")
        else:
            print("❌ Bouton de connexion introuvable.")
    except Exception as e:
        print(f"❌ Erreur lors de la connexion : {e}")
        driver.save_screenshot("login_error.png")
        raise

# Téléchargement d’un export CommCare
def download_file(driver: webdriver.Chrome, url: str, name: str) -> None:
    print(f"\n📄 Téléchargement de « {name} »…")
    driver.get(url)
    try:
        prepare_btn = WebDriverWait(driver, 200).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'))
        )
        prepare_btn.click()
        print("⏳ Préparation du fichier…")
    except Exception as e:
        print(f"❌ Erreur en cliquant sur « Préparer » : {e}")
        return

    try:
        download_xpath = '//*[@id="download-progress"]/div/div/div[2]/div[1]/form/a'
        download_link = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.XPATH, download_xpath))
        )
        download_link.click()
        print("✅ Téléchargement lancé.")
        time.sleep(5)  # temporisation pour le téléchargement
    except Exception as e:
        print(f"❌ Le bouton de téléchargement n’est pas apparu : {e}")

def main() -> None:
    # Initialiser Chrome avec les options appropriées
    driver = build_chrome_driver()
    try:
        login_to_commcare(driver)
        for doc in DOWNLOAD_LINKS:
            download_file(driver, doc["url"], doc["name"])
        print("\n🎉 Pipeline Muso CommCare terminé avec succès.")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Suppression des warnings Python
    warnings.filterwarnings('ignore')
    main()
