#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide des téléchargements CommCare avec correctif pour le figement
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from function import download_files

if __name__ == "__main__":
    print("Début du téléchargement avec correctif anti-figement...")
    print("Les modifications incluent :")
    print("   - Déblocage automatique de l'interface après saisie de date")
    print("   - Gestion du figement du site CommCare")
    print("   - Clics automatiques en dehors des champs")
    print()
    
    try:
        download_files()
        print()
        print("Téléchargement terminé avec succès!")
        print("Le correctif anti-figement a été appliqué pour chaque fichier")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Si le problème persiste :")
        print("   1. Vérifiez que id_cc.env contient EMAIL et PASSWORD")
        print("   2. Testez avec test_date_fix.py d'abord")
        print("   3. Vérifiez votre connexion internet")
