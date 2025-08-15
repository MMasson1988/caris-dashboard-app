# -*- coding: utf-8 -*-
"""
Script pour télécharger tous les exports CommCare avec pauses entre téléchargements
"""

import os
import time
import logging
from datetime import datetime
from function import (
    setup_driver, commcare_login, trigger_and_download, 
    check_file_exists_today, verify_download_success,
    list_files, DOWNLOAD_DIR, EXPORTS, ENV_FILE
)
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)


def download_all_exports():
    """
    Télécharge tous les exports CommCare avec pauses et vérifications
    """
    load_dotenv(ENV_FILE)
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD") or os.getenv("PASSWORD_CC")

    if not email or not password:
        raise RuntimeError(f"EMAIL / PASSWORD introuvables dans {ENV_FILE}")

    logging.info(f"🔐 Authentification avec: {email}")
    logging.info(f"📁 Répertoire de téléchargement: {DOWNLOAD_DIR}")

    driver = setup_driver(DOWNLOAD_DIR)

    try:
        # Login avec le premier export
        first_export = EXPORTS[0]
        logging.info("🔑 Tentative de connexion...")
        commcare_login(driver, email, password, first_export["url"])
        
        # Variables pour le suivi des téléchargements
        results = []
        failed = []
        
        logging.info(f"📥 TÉLÉCHARGEMENT MULTIPLE - {len(EXPORTS)} fichiers à traiter")
        logging.info("=" * 60)
        
        # Traiter chaque export
        for i, export in enumerate(EXPORTS, 1):
            name = export["name"]
            url = export["url"]
            
            # Vérifier si le fichier existe déjà
            exists, existing_path, reason = check_file_exists_today(export, DOWNLOAD_DIR)
            
            if exists:
                logging.info(f"[{i}/{len(EXPORTS)}] ⏭️ {name}")
                logging.info(f"  ✅ Fichier déjà présent: {reason}")
                results.append((name, existing_path))
                continue
            
            logging.info(f"[{i}/{len(EXPORTS)}] 📥 {name}")
            logging.info(f"  🌐 {url}")
            
            # Pause entre les téléchargements (sauf pour le premier)
            if i > 1:
                logging.info("  ⏳ Pause de 8 secondes avant téléchargement...")
                time.sleep(8)
            
            # État avant téléchargement
            before_files = list_files(DOWNLOAD_DIR)
            
            try:
                # Téléchargement
                path = trigger_and_download(driver, url)
                
                # Vérification du succès
                if path and os.path.isfile(path):
                    success, message = verify_download_success(export, DOWNLOAD_DIR, path)
                    
                    if success:
                        logging.info(f"  ✅ Téléchargement réussi: {message}")
                        results.append((name, path))
                    else:
                        logging.error(f"  ❌ Vérification échouée: {message}")
                        failed.append((name, f"Vérification échouée: {message}"))
                else:
                    error_msg = f"Aucun fichier valide retourné (path={path})"
                    logging.error(f"  ❌ {error_msg}")
                    failed.append((name, error_msg))
                    
            except Exception as download_error:
                error_msg = str(download_error)
                logging.error(f"  ❌ Erreur lors du téléchargement: {error_msg}")
                failed.append((name, error_msg))
                
                # Pause plus longue en cas d'erreur
                if i < len(EXPORTS):
                    logging.info("  ⏳ Pause de 15 secondes après erreur...")
                    time.sleep(15)
            
            # État après téléchargement
            after_files = list_files(DOWNLOAD_DIR)
            new_files = after_files - before_files
            
            if new_files:
                logging.info(f"  📄 Nouveaux fichiers: {list(new_files)}")
            
            # Petite pause même en cas de succès
            if i < len(EXPORTS):
                time.sleep(3)
        
        # RAPPORT FINAL
        logging.info("=" * 60)
        logging.info("📊 RAPPORT DE TÉLÉCHARGEMENT MULTIPLE")
        logging.info("=" * 60)
        
        if results:
            logging.info(f"✅ SUCCÈS ({len(results)}):")
            for name, path in results:
                file_size = os.path.getsize(path) if os.path.exists(path) else 0
                logging.info(f"   • {name}")
                logging.info(f"     📄 {os.path.basename(path)} ({file_size:,} bytes)")
        
        if failed:
            logging.info(f"\n❌ ÉCHECS ({len(failed)}):")
            for name, error in failed:
                logging.info(f"   • {name}")
                logging.info(f"     💥 {error}")
        
        # Statistiques finales
        total_files = len(EXPORTS)
        success_count = len(results)
        failure_count = len(failed)
        success_rate = (success_count / total_files) * 100 if total_files > 0 else 0
        
        logging.info(f"\n📈 STATISTIQUES:")
        logging.info(f"   Total: {total_files} fichiers")
        logging.info(f"   Succès: {success_count}")
        logging.info(f"   Échecs: {failure_count}")
        logging.info(f"   Taux de réussite: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logging.info("🎉 TÉLÉCHARGEMENT EXCELLENT!")
        elif success_rate >= 75:
            logging.info("👍 TÉLÉCHARGEMENT SATISFAISANT")
        else:
            logging.warning("⚠️ TÉLÉCHARGEMENT AVEC PROBLÈMES")
        
        return success_rate >= 75

    except Exception as main_error:
        logging.error(f"❌ Erreur principale: {main_error}")
        raise
    finally:
        logging.info("🔒 Fermeture du navigateur...")
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU TÉLÉCHARGEMENT MULTIPLE")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Répertoire: {DOWNLOAD_DIR}")
    print(f"📦 Nombre d'exports: {len(EXPORTS)}")
    print()
    
    try:
        success = download_all_exports()
        
        if success:
            print("\n🎉 TÉLÉCHARGEMENT MULTIPLE TERMINÉ AVEC SUCCÈS!")
        else:
            print("\n⚠️ Téléchargement terminé avec quelques problèmes")
            
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
