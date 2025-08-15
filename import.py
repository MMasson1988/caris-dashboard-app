#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification de l'environnement et des dependances avec gestion automatique des requirements
Auteur : Systeme d'analyse CommCareHQ
Usage : python import.py
"""

import os
import sys
import subprocess

def install_requirements():
    """Installe automatiquement les requirements si necessaire"""
    print("[INSTALL] Verification des dependances...")
    
    # Detecter l'environnement virtuel
    if os.path.exists(".venv/Scripts/python.exe"):
        # Environnement virtuel Windows
        python_exec = ".venv/Scripts/python.exe"
        pip_exec = ".venv/Scripts/pip.exe"
    elif os.path.exists(".venv/bin/python"):
        # Environnement virtuel Unix/Linux
        python_exec = ".venv/bin/python"
        pip_exec = ".venv/bin/pip"
    else:
        # Python système
        python_exec = sys.executable
        pip_exec = "pip"
    
    # Vérifier d'abord si les packages principaux sont installés
    try:
        import pandas, numpy, openpyxl, selenium, dotenv, sqlalchemy
        print("[OK] Packages principaux deja installes!")
        return True
    except ImportError:
        print("[INSTALL] Installation des dependances requise...")
    
    try:
        # Installer les requirements
        result = subprocess.run([pip_exec, "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] Dependances installees avec succes!")
            return True
        else:
            print(f"[WARNING] Problemes lors de l'installation: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'installation: {e}")
        return False

def check_requirements():
    """Verifie si requirements.txt existe et propose l'installation"""
    if os.path.exists("requirements.txt"):
        print("[INFO] Fichier requirements.txt trouve")
        
        # Lire le nombre de packages
        with open("requirements.txt", 'r') as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"[INFO] {len(packages)} packages definis dans requirements.txt")
        return True
    else:
        print("[ERROR] Fichier requirements.txt manquant")
        return False

print("DEBUT DE L'ANALYSE COMMCARE")
print("=" * 60)
print()

# =========================
# 1. VERIFICATION DES REQUIREMENTS
# =========================
print("1. VERIFICATION DES REQUIREMENTS")
print("-" * 40)

requirements_exist = check_requirements()
if requirements_exist:
    # Tentative d'installation automatique des requirements
    install_success = install_requirements()
else:
    install_success = False

print()

# =========================
# 2. VERIFICATION DE L'ENVIRONNEMENT
# =========================
print("2. VERIFICATION DE L'ENVIRONNEMENT")
print("-" * 40)

# Test des imports requis
print("Test des imports...")
modules_requis = [
    ("pandas", "pd"),
    ("numpy", "np"),
    ("openpyxl", None),
    ("selenium", None),
    ("dotenv", None),
    ("sqlalchemy", None)
]

imports_reussis = []
imports_echues = []

for module, alias in modules_requis:
    try:
        if alias:
            exec(f"import {module} as {alias}")
        else:
            exec(f"import {module}")
        imports_reussis.append(module)
        print(f"{module} OK")
    except ImportError as e:
        imports_echues.append(module)
        print(f"{module} FAILED: {e}")

print()

# Test du fichier d'environnement
print("Test du fichier d'environnement...")
env_file = "id_cc.env"
if os.path.exists(env_file):
    print(f"Fichier {env_file} trouve")
else:
    print(f"ATTENTION: Fichier {env_file} manquant")

print()

# Verification du repertoire de donnees
print("Test du repertoire de donnees...")
data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    print(f"Repertoire {data_dir}/ cree")
else:
    print(f"Repertoire {data_dir}/ existe")

print()

# Tentative de chargement des variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv("id_cc.env")
    
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    
    if email:
        print(f"EMAIL trouve: {email[:3]}***")
    else:
        print("EMAIL non trouve")
        
    if password:
        print("PASSWORD trouve")
    else:
        print("PASSWORD non trouve")
        
    print("Variables d'environnement chargees avec succes")
except Exception as e:
    print(f"Avertissements: {e}")
    
print()

# =========================
# RESUME
# =========================
print("=" * 60)
if imports_echues:
    print("VERIFICATION ECHOUEE!")
    print(f"Modules manquants: {', '.join(imports_echues)}")
    if not install_success:
        print("[SOLUTIONS] Solutions proposees:")
        print("   1. Installer manuellement: pip install -r requirements.txt")
        print("   2. Utiliser l'environnement virtuel:")
        print("      .venv/Scripts/pip.exe install -r requirements.txt")
        print("   3. Executer le script d'installation automatique")
else:
    print("VERIFICATION REUSSIE!")
    print("Tous les modules requis sont installes")
    print(f"[OK] {len(imports_reussis)} modules charges avec succes")

print("=" * 60)
