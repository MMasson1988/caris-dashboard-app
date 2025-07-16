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

from datetime import date
import pandas as pd

def save_dataframes_excel(output_name="output", dataframes=None, sheet_names=None):
    """
    Sauvegarde plusieurs DataFrames dans un fichier Excel avec un nom dynamique basé sur la date.

    Args:
        output_name (str): Nom de base du fichier de sortie (sans extension).
        dataframes (list of pd.DataFrame): Liste des DataFrames à sauvegarder.
        sheet_names (list of str, optional): Noms des feuilles Excel correspondantes.
    """
    if not dataframes:
        print("❌ Aucun DataFrame fourni.")
        return

    today_str = date.today().strftime("%Y-%m-%d")
    file_name = f"{output_name}_{today_str}.xlsx"

    if sheet_names and len(sheet_names) != len(dataframes):
        raise ValueError("Le nombre de noms de feuilles ne correspond pas au nombre de DataFrames.")

    sheet_names = sheet_names or [f"Sheet{i+1}" for i in range(len(dataframes))]

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        for df, sheet in zip(dataframes, sheet_names):
            if df is not None:
                df.to_excel(writer, sheet_name=sheet, index=False)

    print(f"✅ Fichier '{file_name}' sauvegardé avec succès.")
#==========================================================================

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

#================================= PHASE II ===============================
# === Configuration ===
load_dotenv('id_cc.env')
email = os.getenv('EMAIL')
password_cc = os.getenv('PASSWORD')
download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
expected_extension = ".xlsx"  # ou ".zip", selon le type de fichier
wait_timeout = 3600  # jusqu'à 1 heure (3600 secondes)

# === Préparer le navigateur ===
options = Options()
prefs = {"download.default_directory": download_dir,
         "download.prompt_for_download": False,
         "directory_upgrade": True}
options.add_experimental_option("prefs", prefs)
options.add_argument("start-maximized")

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

# === Login CommCare ===
def commcare_login():
    driver.get('https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/f831c9c92760a38d24b3829df5621d20/')
    WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.ID, "id_auth-username")))
    driver.find_element(By.ID, "id_auth-username").send_keys(email)
    driver.find_element(By.ID, "id_auth-password").send_keys(password_cc)
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()

commcare_login()

# === Cliquer sur Préparer le fichier ===
WebDriverWait(driver, 500).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'))).click()

# === Cliquer sur le lien de téléchargement ===
WebDriverWait(driver, 2000).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="download-progress"]/div/div/div[2]/div[1]/form/a'))).click()

# === Attendre que le fichier apparaisse complètement dans le dossier ===
def wait_for_download(folder, extension, timeout):
    seconds = 0
    while seconds < timeout:
        files = glob.glob(os.path.join(folder, f"*{extension}"))
        if files:
            if not any(f.endswith(".crdownload") or f.endswith(".part") for f in files):
                print("✅ Téléchargement terminé :", os.path.basename(files[0]))
                return
        time.sleep(10)
        seconds += 10
    raise TimeoutError("⏰ Temps d'attente dépassé pour le téléchargement.")

wait_for_download(download_dir, expected_extension, wait_timeout)
#=================================== PHASE III ==============================
muso_group = pd.read_excel(f"~/Downloads/muso_groupes (created 2025-03-25) {str(datetime.today().strftime('%Y-%m-%d'))}.xlsx", parse_dates = True)
muso_ben = pd.read_excel(f"~/Downloads/muso_beneficiaries (created 2025-03-25) {str(datetime.today().strftime('%Y-%m-%d'))}.xlsx", parse_dates = True)
muso_household = pd.read_excel(f"~/Downloads/muso_household_2022 (created 2025-03-25) {str(datetime.today().strftime('%Y-%m-%d'))}.xlsx", parse_dates = True)
muso_ppi = pd.read_excel(f"~/Downloads/MUSO - Members - PPI Questionnaires (created 2025-04-23) {str(datetime.today().strftime('%Y-%m-%d'))}.xlsx", parse_dates = True)
muso_actif = pd.read_excel(f"./group_muso_actif.xlsx", parse_dates = True)

# Ensure both DataFrames have the 'caseid' column and drop NA values before filtering
if 'caseid' in muso_actif.columns and 'caseid' in muso_group.columns:
    muso_group_caseids = muso_actif['caseid'].dropna().unique()
    muso_group_actif = muso_group[muso_group['caseid'].isin(muso_group_caseids)]
    print(muso_group_actif.shape[0])
else:
    print("Erreur : 'caseid' colonne manquante dans muso_actif ou muso_group")
    

muso_group_actif["opened_by_username"] = muso_group_actif["opened_by_username"].replace(
    "pierrerobentz.cassion@carisfoundationintl.org", "2estheve"
)

# Renommage de la colonne
muso_group_actif = muso_group_actif.rename(columns={"opened_by_username": "username"})


muso_group_actif.value_counts("username")

# Liste d'en-têtes (tu peux copier directement depuis ta source)
colonnes = [ "caseid", "is_graduated", "office", "graduation_date", "commune_name",
    "code", "creation_date", "officer_name", "gps_date", "gps", "office_name", "adress",
    "section_name", "departement_name", "name", "present", "credit", "balance", "absent",
    "cotisation", "date_suivi", "date_prochain_suivi", "closed", "closed_by_username",
    "last_modified_date", "username", "opened_date",
    "owner_name", "case_link"]
muso_group_actif = muso_group_actif[colonnes].reset_index(drop=True)

# Afficher les premières colonnes pour vérification
#print(muso_group_actif.head(2))

muso_group_actif.to_excel("muso_group_actif.xlsx")

# Ensure both DataFrames have the 'caseid' column and drop NA values before filtering
if 'caseid_group' in muso_group_actif.columns and 'caseid_group' in muso_ben.columns:
    muso_group_caseids = muso_group_actif['caseid_group'].dropna().unique()
    muso_ben_actif = muso_ben[muso_ben['caseid_group'].isin(muso_group_caseids)]
    print(f"Number of muso beneficiaries: {muso_ben_actif.shape[0]}")
else:
    print("Erreur : 'caseid_group' colonne manquante dans muso_actif ou muso_group")


muso_pvvih = muso_ben_actif[muso_ben_actif["is_pvvih"]=="1"]
print(f"Number of PVVIH in muso : {muso_pvvih.shape[0]}")

#=========================================================================
#                               FIN
driver.quit()
#=========================================================================
