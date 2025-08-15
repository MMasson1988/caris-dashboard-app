#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal d'analyse utilisant uniquement import.py, function.py, et download.py
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

# 1. Vérification des imports et de l'environnement
print("="*50)
print("ÉTAPE 1: Vérification de l'environnement")
print("="*50)
import subprocess
result = subprocess.run([sys.executable, "import.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Avertissements:", result.stderr)

# 2. Import des fonctions depuis function.py
print("\n" + "="*50)
print("ÉTAPE 2: Import des fonctions d'analyse")
print("="*50)
from function import download_files
import pandas as pd
from datetime import datetime

# Vérification des fichiers attendus avant téléchargement
today_date = datetime.today().date().strftime('%Y-%m-%d')
base_path = r"C:\Users\Moise\Downloads\Call-App\data"
expected_files = [
    f"Caris Health Agent - Femme PMTE  - APPELS PTME (created 2025-02-13) {today_date}.xlsx",
    f"Caris Health Agent - Enfant - APPELS OEV (created 2025-01-08) {today_date}.xlsx",
    f"Caris Health Agent - Femme PMTE  - Visite PTME (created 2025-02-13) {today_date}.xlsx",
    f"Caris Health Agent - Femme PMTE  - Ration & Autres Visites (created 2025-02-18) {today_date}.xlsx",
    f"Caris Health Agent - Enfant - Ration et autres visites (created 2022-08-29) {today_date}.xlsx",
    f"Caris Health Agent - Enfant - Visite Enfant (created 2025-07-30) {today_date}.xlsx",
]
missing_files = [f for f in expected_files if not os.path.exists(os.path.join(base_path, f))]

# 3. Téléchargement des fichiers via download.py
print("\n" + "="*50)
print("ÉTAPE 3: Téléchargement des données CommCare")
print("="*50)
if missing_files:
    print(f"Fichiers manquants: {missing_files}")
    try:
        download_files()
        print("✅ Téléchargement terminé avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("✅ Tous les fichiers sont déjà présents, téléchargement ignoré.")

# 4. Analyse des données
print("\n" + "="*50)
print("ÉTAPE 4: Analyse des données téléchargées")
print("="*50)

# Variables de configuration
today_date = datetime.today().date().strftime('%Y-%m-%d')
start_date = pd.to_datetime('2025-01-01')
end_date = pd.to_datetime('2025-08-11')
base_path = r"C:\Users\Moise\Downloads\Call-App\data"

# Importation des données
try:
    print("📊 Chargement des fichiers de données...")
    
    # Import dial dataset
    Apel_ptme = pd.read_excel(f"{base_path}/Caris Health Agent - Femme PMTE  - APPELS PTME (created 2025-02-13) {today_date}.xlsx", parse_dates=True)
    Apel_oev = pd.read_excel(f"{base_path}/Caris Health Agent - Enfant - APPELS OEV (created 2025-01-08) {today_date}.xlsx", parse_dates=True)
    
    # Import visit dataset
    Visite_ptme = pd.read_excel(f"{base_path}/Caris Health Agent - Femme PMTE  - Visite PTME (created 2025-02-13) {today_date}.xlsx", parse_dates=True)
    Ration_ptme = pd.read_excel(f"{base_path}/Caris Health Agent - Femme PMTE  - Ration & Autres Visites (created 2025-02-18) {today_date}.xlsx", parse_dates=True)
    Ration_oev = pd.read_excel(f"{base_path}/Caris Health Agent - Enfant - Ration et autres visites (created 2022-08-29) {today_date}.xlsx", parse_dates=True)
    oev_visite = pd.read_excel(f"{base_path}/Caris Health Agent - Enfant - Visite Enfant (created 2025-07-30) {today_date}.xlsx", parse_dates=True)
    
    print("✅ Tous les fichiers ont été chargés avec succès!")
    print(f"📈 Nombre d'enregistrements:")
    print(f"   - Appels PTME: {len(Apel_ptme)}")
    print(f"   - Appels OEV: {len(Apel_oev)}")
    print(f"   - Visites PTME: {len(Visite_ptme)}")
    print(f"   - Rations PTME: {len(Ration_ptme)}")
    print(f"   - Rations OEV: {len(Ration_oev)}")
    print(f"   - Visites OEV: {len(oev_visite)}")
    
except FileNotFoundError as e:
    print(f"❌ Fichier non trouvé: {e}")
    print("💡 Vérifiez que le téléchargement s'est bien déroulé")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur lors du chargement des données: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("ANALYSE TERMINÉE AVEC SUCCÈS!")
print("="*50)
print("🎯 Les données sont maintenant prêtes pour l'analyse dans le notebook")
print("📁 Répertoire des données:", base_path)
print("📅 Période d'analyse: {} à {}".format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
