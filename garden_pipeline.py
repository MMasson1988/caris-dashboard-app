#!/usr/bin/env python
# coding: utf-8

import os
import subprocess
import warnings
import time
from datetime import datetime, date
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import get_commcare_odata
from ptme_fonction import creer_colonne_match_conditional

warnings.filterwarnings('ignore')


# --- UTILS ---

def run_shell_script(script_path):
    if not os.path.exists(script_path):
        print(f"⚠️ Script introuvable : {script_path}")
        return
    print(f"🟢 Exécution du script shell : {script_path}")
    result = subprocess.run(["bash", script_path], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Script exécuté avec succès.")
    else:
        print(f"❌ Erreur lors de l'exécution :\n{result.stderr}")
    print(result.stdout)


def save_dataframes_excel(output_name="output", df_list=None, sheet_names=None):
    if df_list is None:
        df_list = []
    if sheet_names is None:
        sheet_names = [f"Sheet{i+1}" for i in range(len(df_list))]
    today_str = date.today().strftime("%Y-%m-%d")
    file_name = f"{output_name}_{today_str}.xlsx"
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        for df, sheet in zip(df_list, sheet_names):
            if df is not None:
                df.to_excel(writer, sheet_name=sheet, index=False)
    print(f"📁 Fichier sauvegardé : {file_name}")


def selenium_download_commcare():
    load_dotenv('id_cc.env')
    email = os.getenv('EMAIL')
    password_cc = os.getenv('PASSWORD')

    options = Options()
    options.add_argument("start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 120)

    try:
        driver.get("https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/789629a97bddd10b4648d5138d17908e/")
        wait.until(EC.presence_of_element_located((By.ID, "id_auth-username"))).send_keys(email)
        driver.find_element(By.ID, "id_auth-password").send_keys(password_cc)
        driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()

        prepare_btn = '//*[@id="download-export-form"]/form/div[2]/div/div[2]/div[1]/button'
        wait.until(EC.element_to_be_clickable((By.XPATH, prepare_btn))).click()

        download_link = '//*[@id="download-progress"]//form/a'
        wait.until(EC.element_to_be_clickable((By.XPATH, download_link))).click()
        print("⏳ Attente du téléchargement...")
        time.sleep(30)
    except Exception as e:
        print(f"❌ Erreur Selenium : {e}")
    finally:
        driver.quit()


# --- MAIN PIPELINE ---
def main():
    print("🚀 Début de l'exécution du pipeline...")

    run_shell_script("./run_commcare.sh")
    run_shell_script("./run_odata.sh")

    selenium_download_commcare()

    load_dotenv('id_cc.env')
    auth = (os.getenv('CC_USERNAME'), os.getenv('CC_PASSWORD'))
    garden_url = 'https://www.commcarehq.org/a/caris-test/api/odata/cases/v1/30eff12a21b721802a814346a46bd970/feed'
    
    try:
        garden_household = get_commcare_odata(garden_url, auth, {})
        df_hh = pd.DataFrame(garden_household)
        df_hh.columns = [col.replace(' ', '_') for col in df_hh.columns]
        cols_hh = ['indices_Garden','age_in_year','gender','gardining_member_relationship',
                   'hiv_test','hiv_test_date','hiv_test_result','is_on_arv','risk_level',
                   'referred_for_a_test','test_institution']
        df_hh = df_hh[cols_hh]
        df_hh.to_excel("garden_household.xlsx", index=False)
        print("✅ Fichier household exporté.")
    except Exception as e:
        print(f"❌ Erreur import Garden Household : {e}")

    today_str = datetime.today().strftime('%Y-%m-%d')
    garden_path = os.path.expanduser(f"~/Downloads/All Gardens {today_str}.xlsx")
    if not os.path.exists(garden_path):
        print(f"❌ Fichier Garden introuvable : {garden_path}")
        return

    df = pd.read_excel(garden_path)
    df.rename(columns={'info.case_id': 'caseid', 'info.owner_name': 'owner_name'}, inplace=True)

    infos = pd.read_excel('site_info.xlsx', usecols=['site', 'status', 'network', 'commune', 'departement', 'office'])
    infos['site'] = infos['site'].astype(str).str.strip()

    df['site'] = df['caris_site'].astype(str).str.split('-').str[0].str.strip()
    df = pd.merge(df, infos, on='site', how='left')

    for col, val in {
        'office': 'GON',
        'site': 'ZLS/POZS',
        'departement': 'Artibonite',
        'commune': "L'Estere",
        'network': 'santé'
    }.items():
        df[col] = df[col].fillna(val)

    for col in ['dat_gradyasyon', 'info.last_modified_date', 'cycle_4_start_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df['closed'] = df['closed'].astype(str).str.strip().str.lower()

    start_date = pd.to_datetime('2025-01-24')
    end_date = pd.to_datetime('2025-03-30')
    start_date_last = pd.to_datetime('2025-04-01')
    end_date_last = pd.to_datetime('2025-06-30')

    date_columns_garden = ['cycle_1_start_date', 'cycle_2_start_date', 'cycle_3_start_date', 'cycle_4_start_date']

    graduated = df[(df['dat_gradyasyon'] >= start_date) & (df['dat_gradyasyon'] <= end_date_last)]
    print(f"Nombre de bénéficiaires gradués : {graduated.shape[0]}")
    graduated.to_excel("graduated.xlsx", index=False)

    for col in date_columns_garden:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    filtered_garden = df[
        df[date_columns_garden].apply(lambda row: any((row >= start_date) & (row <= end_date)), axis=1)
    ].drop_duplicates(subset='caseid')

    print(f"Nombre de cas filtrés dans filtered_garden : {filtered_garden.shape[0]}")
    filtered_garden.to_excel("filtered_garden.xlsx", index=False)

    first_period = df[(df['info.last_modified_date'] >= start_date) & (df['info.last_modified_date'] <= end_date) & (df['closed'] == 'false')]
    second_period = df[(df['info.last_modified_date'] >= start_date_last) & (df['info.last_modified_date'] <= end_date_last) & (df['closed'] == 'false')]

    second_period1 = second_period[second_period['cycle_4_start_date'].isna() | (second_period['cycle_4_start_date'] == pd.Timestamp(0))]
    second_period2 = second_period[(second_period['cycle_4_start_date'] < start_date) | (second_period['cycle_4_start_date'] > end_date)]

    df_1 = first_period.copy()
    df_1['periode'] = 'first_period'

    df_2 = pd.concat([second_period1, second_period2], ignore_index=True)
    df_2['periode'] = 'second_period'

    df_final = pd.concat([df_1, df_2], ignore_index=True)

    df_final.rename(columns={'st_code': 'patient_code', 'erk_achte_te': 'autres_terrain'}, inplace=True)

    all_gardens = df_final[(df_final['office'] != 'Jeremie') & (df_final['office'] != 'Cayes')].copy()

    garden_date_cols = [
        'statut', 'caris_site', 'start_date', 'cycle_1_end_date', 'cycle_1_start_date',
        'cycle_2_end_date', 'cycle_2_start_date', 'cycle_3_end_date', 'cycle_3_start_date',
        'cycle_4_end_date', 'cycle_4_start_date', 'dat_gradyasyon', 'dat_nesans',
        'date_evalyasyon_ranfòsman_kapasite', 'end_date', 'hh_date', 'household_collection_date',
        'closed_date', 'info.last_modified_date', 'owner_name'
    ]

    for col in garden_date_cols:
        if col in all_gardens.columns:
            all_gardens[col] = pd.to_datetime(all_gardens[col].astype(str), errors='coerce')

    garden_numeric_cols = ['age', 'cycle_number', 'hm_household_size', 'total_beneficiaire', 'visit_number']
    for col in garden_numeric_cols:
        if col in all_gardens.columns:
            all_gardens[col] = pd.to_numeric(all_gardens[col].astype(str), errors='coerce')

    garden_string_cols = list(set(all_gardens.columns) - set(garden_date_cols) - set(garden_numeric_cols))
    for col in garden_string_cols:
        all_gardens[col] = all_gardens[col].astype(str)

    cycle_columns = [f'cycle_{i}' for i in range(8)]
    date_columns_by_cycle = {
        'cycle_0': ['start_date'],
        'cycle_1': ['cycle_1_start_date', 'cycle_1_end_date'],
        'cycle_2': ['cycle_2_start_date', 'cycle_2_end_date'],
        'cycle_3': ['cycle_3_start_date', 'cycle_3_end_date'],
        'cycle_4': ['cycle_4_start_date', 'cycle_4_end_date'],
        'cycle_5': ['end_date'],
        'cycle_6': ['dat_gradyasyon'],
        'cycle_7': ['date_evalyasyon_ranfòsman_kapasite']
    }

    for cycle in cycle_columns:
        if cycle not in all_gardens.columns:
            all_gardens[cycle] = "no"
        for date_col in date_columns_by_cycle.get(cycle, []):
            if date_col in all_gardens.columns:
                all_gardens[date_col] = pd.to_datetime(all_gardens[date_col], errors='coerce')
                all_gardens.loc[
                    (all_gardens[date_col] >= start_date) & (all_gardens[date_col] <= end_date),
                    cycle
                ] = "yes"

    for i in range(8):
        cycle_col = f'cycle_{i}'
        df_cycle = all_gardens[all_gardens[cycle_col] == 'yes'].copy()
        globals()[f'dataframe_cycle_{i}'] = df_cycle
        print(f"Cycle {i}: {df_cycle.shape[0]} enregistrements")

    info_garden = df[['caseid', 'owner_name']].drop_duplicates(subset='caseid').rename(columns={'owner_name': 'username'})

    all_gardens = pd.merge(all_gardens, info_garden, on='caseid', how='left')
    all_gardens['statut'] = np.where(all_gardens['beneficiary_type'] == 'Caris', 'positif', 'indetermine')
    all_gardens = all_gardens[(all_gardens['cycle_4_start_date'] <= start_date) & (all_gardens['cycle_4_end_date'] <= start_date)]

    # Liste cible des techniciens
    username = [
        "1mackenson",
        "j6geniel",
        "j1james",
        "6jkenson",
        "j6emanise",
        "j1cepoudy",
        "j1vincent",
        "j1napolean",
        "j6benest",
        "j6guerby"
    ]
    all_gardens = all_gardens[all_gardens['username'].isin(username)]
    all_gardens.to_excel('all_gardens.xlsx', index=False)
    print(f"✅ Nombre total de bénéficiaires dans all_gardens : {all_gardens.shape[0]}")
    print("✅ Pipeline terminé. Fichier : all_gardens.xlsx")
if __name__ == "__main__":
    main()
