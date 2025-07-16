
# Standard library imports
import os
import re
import time
import warnings
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# Third-party imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import openpyxl
import xlsxwriter
import pymysql
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
# import functions
from utils import get_commcare_odata
# Download charges virales database from "Charges_virales_pediatriques.sql file"
from caris_fonctions import execute_sql_query

# Load environment variables from .env file
load_dotenv('dot.env')
pd.set_option('display.float_format', '{:.2f}'.format)  # Set float format
# Suppress warnings
warnings.filterwarnings('ignore')


# Chargement des identifiants CommCare
load_dotenv("id_cc.env")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Configuration du navigateur (sans dossier de téléchargement personnalisé)
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

# Liste des liens à télécharger
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

# 🔐 Connexion à CommCare
def login_to_commcare():
    print("🔐 Connexion à CommCare...")
    driver.get(DOWNLOAD_LINKS[0]["url"])
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "id_auth-username")))
    driver.find_element(By.ID, "id_auth-username").send_keys(EMAIL)
    driver.find_element(By.ID, "id_auth-password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
    print("✅ Connexion réussie.")

# 📥 Téléchargement d’un export CommCare
def download_file(url, name):
    print(f"\n📄 Téléchargement de « {name} »...")
    driver.get(url)

    try:
        WebDriverWait(driver, 200).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'))
        ).click()
        print("⏳ Préparation du fichier...")
    except Exception as e:
        print(f"❌ Erreur en cliquant sur « Préparer » : {e}")
        return

    try:
        download_xpath = '//*[@id="download-progress"]/div/div/div[2]/div[1]/form/a'
        WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.XPATH, download_xpath))
        ).click()
        print("✅ Téléchargement lancé.")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Le bouton de téléchargement n’est pas apparu : {e}")

# 🧠 Fonction principale
def main():
    login_to_commcare()
    
    for doc in DOWNLOAD_LINKS:
        download_file(doc["url"], doc["name"])

    print("\n🎉 Pipeline Muso CommCare terminé avec succès.")

if __name__ == "__main__":
    main()

#================================= PHASE II ==============================
