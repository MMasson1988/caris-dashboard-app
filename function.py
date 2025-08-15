# -*- coding: utf-8 -*-
"""
Automation CommCare + SQL utilitaires
Auteur : Masson
Prérequis :
  pip install python-dotenv selenium sqlalchemy pymysql pandas

ENV attendus :
  EMAIL=...
  PASSWORD=...
  # pour SQL (optionnel si vous utilisez execute_sql_query)
  MYSQL_USER=...
  MYSQL_PASSWORD=...
  MYSQL_HOST=...
  MYSQL_DB=...
  # optionnel
  HEADLESS=0|1
"""

import os
import time
import logging
import re
import glob
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# --- SQL (optionnel) ---
from sqlalchemy import create_engine

# --- Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


# =========================
# CONFIG UTILISATEUR
# =========================
DOWNLOAD_DIR = r"C:\Users\moise\Downloads\caris-dashboard-app\data"  # Corrigé: utilisé le bon répertoire
ENV_FILE = "id_cc.env"  # doit contenir EMAIL / PASSWORD

EXPORTS = [
    {
        "name": "Enfant - Visite Enfant (2025-07-30)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/7d960d6c03d9d6c35a8d083c288e7c8d/"
    },
    {
        "name": "Enfant - APPELS OEV (2025-01-08)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/f817d728df7d0070b29160e54a22765b/"
    },
    {
        "name": "PTME - Visite PTME (2025-02-13)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/4fde80e15e96e8214eb58d5761049f0f/"
    },
    {
        "name": "PTME - Ration & Autres Visites (2025-02-18)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c5c5e2292ad223156f72620c6e0fd99f/"
    },
    {
        "name": "Enfant - Ration & autres visites (2022-08-29)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/bc95b54ff93a6c62c22a2e2f17852a90/"
    },
    {
        "name": "PTME - APPELS PTME (2025-02-13)",
        "url": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c1a3280f5e34a2b6078439f9b59ad72c/"
    },
]


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)


# =========================
# UTILITAIRES SQL (optionnel)
# =========================
def execute_sql_query(env_path: str, sql_file_path: str) -> pd.DataFrame:
    """Exécute un fichier SQL et retourne un DataFrame."""
    load_dotenv(env_path)
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    db = os.getenv('MYSQL_DB')

    if not all([user, password, host, db]):
        raise RuntimeError("Variables SQL manquantes dans l'env.")

    conn_text = f'mysql+pymysql://{user}:{password}@{host}/{db}'
    engine = create_engine(conn_text)

    with open(sql_file_path, 'r', encoding="utf-8") as f:
        sql_query = f.read().replace('use caris_db;', '')

    df = pd.read_sql_query(sql_query, engine)
    engine.dispose()
    return df


# =========================
# UTILITAIRES FICHIERS
# =========================
def list_files(path: str):
    try:
        return set(os.listdir(path))
    except FileNotFoundError:
        return set()


def wait_for_download_complete(download_dir: str, before_files, timeout: int = 600) -> str:
    """
    Attend l'apparition d'au moins un nouveau fichier ET la disparition des .crdownload.
    Retourne le chemin du fichier le plus récent.
    Amélioration: nettoyage automatique des fichiers .crdownload orphelins et gestion robuste
    """
    start = time.time()
    logging.info(f"Attente du téléchargement dans {download_dir}...")
    
    # Nettoyer d'abord les anciens fichiers .crdownload
    initial_crdownloads = [f for f in list_files(download_dir) if f.endswith(".crdownload")]
    if initial_crdownloads:
        logging.info(f"Nettoyage des anciens fichiers .crdownload: {initial_crdownloads}")
        for crfile in initial_crdownloads:
            try:
                crpath = os.path.join(download_dir, crfile)
                os.remove(crpath)
                logging.info(f"Fichier .crdownload supprimé: {crfile}")
            except Exception as e:
                logging.warning(f"Impossible de supprimer {crfile}: {e}")
    
    # Attendre le nouveau téléchargement
    last_check_time = start
    consecutive_same_files = 0
    
    while True:
        now_files = list_files(download_dir)
        new_files = now_files - before_files
        crdownload_files = [f for f in now_files if f.endswith(".crdownload")]
        
        current_time = time.time()
        
        # Si on a de nouveaux fichiers sans .crdownload, c'est terminé
        if new_files and not crdownload_files:
            latest = max(
                (os.path.join(download_dir, f) for f in new_files if not f.endswith('.crdownload')),
                key=lambda p: os.path.getmtime(p),
            )
            logging.info(f"Téléchargement terminé: {os.path.basename(latest)}")
            return latest
        
        # Gestion des fichiers .crdownload qui traînent
        if crdownload_files:
            # Si les fichiers .crdownload n'ont pas changé pendant 2 minutes, on les supprime
            if current_time - last_check_time > 120:
                logging.warning(f"Fichiers .crdownload stagnants détectés: {crdownload_files}")
                for crfile in crdownload_files:
                    try:
                        crpath = os.path.join(download_dir, crfile)
                        file_size = os.path.getsize(crpath)
                        logging.info(f"Taille du fichier {crfile}: {file_size} bytes")
                        
                        # Si le fichier n'a pas changé de taille, le supprimer
                        if file_size == 0 or current_time - os.path.getmtime(crpath) > 180:
                            os.remove(crpath)
                            logging.info(f"Fichier .crdownload bloqué supprimé: {crfile}")
                    except Exception as e:
                        logging.warning(f"Erreur lors de la gestion de {crfile}: {e}")
                
                last_check_time = current_time
        
        # Timeout global
        if current_time - start > timeout:
            if crdownload_files:
                logging.error(f"Timeout avec fichiers .crdownload persistants: {crdownload_files}")
                # Dernier effort pour nettoyer
                for crfile in crdownload_files:
                    try:
                        os.remove(os.path.join(download_dir, crfile))
                    except:
                        pass
            
            # Vérifier s'il y a quand même de nouveaux fichiers complets
            complete_new_files = [f for f in new_files if not f.endswith('.crdownload')]
            if complete_new_files:
                latest = max(
                    (os.path.join(download_dir, f) for f in complete_new_files),
                    key=lambda p: os.path.getmtime(p),
                )
                logging.warning(f"Timeout mais fichier trouvé: {os.path.basename(latest)}")
                return latest
            
            raise TimeoutException(f"Téléchargement trop long (> {timeout}s)")

        time.sleep(5)  # Vérification toutes les 5 secondes


def check_files(expected_files, base_path=DOWNLOAD_DIR):
    """Diagnostic simple : liste les fichiers attendus manquants."""
    missing = []
    for f in expected_files:
        full_path = os.path.join(base_path, f)
        logging.info(f"Vérification : {full_path}")
        if not os.path.isfile(full_path):
            missing.append(f)
    if missing:
        logging.warning("Fichiers manquants : %s", missing)
    else:
        logging.info("Tous les fichiers attendus sont présents.")


# =========================
# SELENIUM : SETUP + LOGIN + EXPORT
# =========================
def setup_driver(download_dir: str) -> webdriver.Chrome:
    """Configuration du driver Chrome avec diagnostics améliorés"""
    os.makedirs(download_dir, exist_ok=True)
    logging.info(f"Répertoire de téléchargement configuré: {download_dir}")
    
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    
    # Mode headless optionnel
    load_dotenv(ENV_FILE)
    headless_mode = (os.getenv("HEADLESS") or "0").strip() == "1"
    if headless_mode:
        opts.add_argument("--headless=new")
        logging.info("Mode headless activé")
    else:
        logging.info("Mode graphique activé")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,  # Désactiver pour éviter les blocages
        "profile.default_content_settings.popups": 0,
    }
    opts.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(180)  # Augmenté à 3 minutes
        driver.implicitly_wait(10)
        
        # Test basique pour vérifier que le driver fonctionne
        driver.get("about:blank")
        logging.info("Driver Chrome configuré et testé avec succès")
        
        return driver
    except Exception as e:
        logging.error(f"Erreur lors de la configuration du driver Chrome: {e}")
        raise


def wait_click(driver, locator, timeout=60):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    el.click()
    return el


def wait_visible(driver, locator, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


def unfreeze_interface(driver):
    """
    Fonction utilitaire pour débloquer l'interface quand elle reste figée
    Utilise plusieurs techniques pour forcer l'interaction
    """
    try:
        logging.info("Déblocage de l'interface...")
        
        # Technique 1: Cliquer sur le body
        body = driver.find_element(By.TAG_NAME, "body")
        driver.execute_script("arguments[0].click();", body)
        time.sleep(1)
        
        # Technique 2: Simuler un mouvement de souris
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.move_by_offset(50, 50).click().perform()
        time.sleep(0.5)
        actions.move_by_offset(-50, -50).perform()
        
        # Technique 3: Envoyer une touche neutre (Escape)
        body.send_keys(Keys.ESCAPE)
        time.sleep(0.5)
        
        # Technique 4: Focus sur un élément visible
        try:
            focusable_elements = driver.find_elements(By.CSS_SELECTOR, "input, button, select, textarea, a")
            if focusable_elements:
                driver.execute_script("arguments[0].focus();", focusable_elements[0])
                time.sleep(0.5)
        except:
            pass
            
        logging.info("Interface débloquée")
        
    except Exception as e:
        logging.warning(f"Erreur lors du déblocage de l'interface : {e}")


def commcare_login(driver, email: str, password: str, first_export_url: str):
    """
    Ouvre la page d'export → redirection login → saisie credentials
    Clique sur le bouton SUBMIT du formulaire QUI CONTIENT le champ username.
    """
    driver.get(first_export_url)

    user = wait_visible(driver, (By.ID, "id_auth-username"), timeout=60)
    pwd = wait_visible(driver, (By.ID, "id_auth-password"), timeout=60)

    user.clear(); user.send_keys(email.strip())
    pwd.clear();  pwd.send_keys(password.strip())

    # Sélecteur scoppé : on soumet le *bon* formulaire (pas le header langue)
    login_btn = driver.find_element(
        By.XPATH,
        "//form[.//input[@id='id_auth-username']]//button[@type='submit']"
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_btn)
    login_btn.click()

    # Fallback si rien ne part : ENTER dans le champ password
    try:
        WebDriverWait(driver, 2).until(lambda d: "/login" not in d.current_url)
    except Exception:
        pwd.send_keys(Keys.RETURN)

    # Attendre la sortie de /login ou la présence du conteneur d'export
    try:
        WebDriverWait(driver, 30).until(
            lambda d: ("/login" not in d.current_url) or bool(d.find_elements(By.ID, "download-export-form"))
        )
        logging.info("Authentification réussie.")
    except TimeoutException:
        # Débogage : tenter de lire un message d’erreur
        err = ""
        for sel in [".alert.alert-warning", ".alert.alert-danger", ".help-block .errorlist", ".alert.alert-info"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                err = els[0].text
                break
        raise RuntimeError(f"Échec d’authentification (toujours sur /login). Message éventuel: {err!r}")


def set_date_range(driver, start_date="2025-01-01", end_date="2025-08-11"):
    """
    Définit la plage de dates dans le formulaire CommCare
    Gère le comportement figé du site en cliquant en dehors du champ
    """
    try:
        # Attendre que le champ de date soit visible
        date_input = wait_visible(driver, (By.ID, "id_date_range"), timeout=30)
        
        # Cliquer sur le champ pour le focus
        date_input.click()
        time.sleep(0.5)
        
        # Effacer complètement le champ
        date_input.clear()
        time.sleep(0.5)
        
        # Sélectionner tout le contenu et le supprimer au cas où
        date_input.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        date_input.send_keys(Keys.DELETE)
        time.sleep(0.5)
        
        # Saisir la nouvelle plage de dates
        date_range_value = f"{start_date} to {end_date}"
        date_input.send_keys(date_range_value)
        
        logging.info(f"Plage de dates saisie : {date_range_value}")
        
        # SOLUTION pour le site figé : utiliser la fonction de déblocage
        time.sleep(1)  # Laisser le temps à la saisie de se finaliser
        
        # Sortir du champ avec TAB
        date_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # Débloquer l'interface avec notre fonction spécialisée
        unfreeze_interface(driver)
        
        # Vérifier que la valeur a été correctement saisie
        try:
            current_value = date_input.get_attribute("value")
            if date_range_value not in current_value:
                logging.warning("La valeur de date ne semble pas prise en compte, nouvelle tentative...")
                date_input.clear()
                time.sleep(0.3)
                date_input.send_keys(date_range_value)
                date_input.send_keys(Keys.TAB)
                time.sleep(1)
                unfreeze_interface(driver)
        except Exception as ve:
            logging.warning(f"Impossible de vérifier la valeur du champ date : {ve}")
        
        # Pause finale pour s'assurer que l'interface est stable
        time.sleep(2)
        
        logging.info(f"Plage de dates définie et interface débloquée : {date_range_value}")
        
    except TimeoutException:
        logging.warning("Impossible de définir la plage de dates - champ non trouvé")
    except Exception as e:
        logging.warning(f"Erreur lors de la définition de la plage de dates : {e}")
        # En cas d'erreur, essayer de débloquer l'interface quand même
        try:
            unfreeze_interface(driver)
        except:
            pass


def trigger_and_download(driver, export_url: str) -> str:
    """
    Version améliorée avec plus de diagnostics et robustesse
    """
    logging.info(f"🌐 Accès à l'URL d'export : {export_url}")
    
    try:
        driver.get(export_url)
        
        # Vérifier que la page s'est bien chargée
        current_url = driver.current_url
        logging.info(f"Page chargée: {current_url}")
        
        # Attendre que la page soit complètement chargée
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)
        
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la page: {e}")
        raise
    
    # Vérifier si on est bien sur une page d'export
    try:
        page_title = driver.title
        logging.info(f"Titre de la page: {page_title}")
        
        if "login" in driver.current_url.lower():
            logging.error("Redirection vers la page de login détectée - problème d'authentification")
            raise RuntimeError("Problème d'authentification - redirection vers login")
            
    except Exception as e:
        logging.warning(f"Impossible de vérifier le titre de la page: {e}")
    
    # Définir la plage de dates avant de préparer l'export
    logging.info("📅 Définition de la plage de dates...")
    try:
        set_date_range(driver, "2025-01-01", "2025-08-11")
    except Exception as e:
        logging.warning(f"Erreur lors de la définition des dates: {e}")
        # Continuer même si les dates ne peuvent pas être définies
    
    # Attendre un peu plus pour s'assurer que l'interface est débloquée
    logging.info("⏳ Attente stabilisation de l'interface...")
    time.sleep(5)
    
    # Vérifier que le formulaire d'export est présent
    try:
        export_form = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "download-export-form"))
        )
        if export_form.is_displayed():
            logging.info("✅ Formulaire d'export trouvé et visible")
        else:
            logging.warning("⚠️ Formulaire d'export trouvé mais pas visible")
            time.sleep(5)
    except TimeoutException:
        logging.error("❌ Formulaire d'export non trouvé!")
        # Diagnostic: lister tous les formulaires présents
        try:
            all_forms = driver.find_elements(By.TAG_NAME, "form")
            logging.info(f"Formulaires détectés sur la page: {len(all_forms)}")
            for i, form in enumerate(all_forms):
                form_id = form.get_attribute("id") or "sans-id"
                form_class = form.get_attribute("class") or "sans-classe"
                logging.info(f"  Formulaire {i+1}: id='{form_id}', class='{form_class}'")
        except Exception as diag_error:
            logging.error(f"Erreur lors du diagnostic: {diag_error}")
        
        raise TimeoutException("Formulaire d'export introuvable")

    # Capturer l'état des fichiers avant téléchargement
    before = list_files(DOWNLOAD_DIR)
    logging.info(f"📁 Fichiers avant téléchargement: {len(before)}")

    # 1) Bouton Prepare/Download avec diagnostic amélioré
    logging.info("🔘 Recherche du bouton de préparation...")
    prepare_locators = [
        (By.CSS_SELECTOR, "#download-export-form button[type='submit']"),
        (By.CSS_SELECTOR, "#download-export-form .btn-primary"),
        (By.CSS_SELECTOR, "#download-export-form button"),
        (By.XPATH, "//div[@id='download-export-form']//button[contains(@class,'btn')]"),
        (By.XPATH, "//form//button[contains(text(),'Prepare') or contains(text(),'Export')]"),
    ]
    
    button_clicked = False
    for i, loc in enumerate(prepare_locators):
        try:
            logging.info(f"  Tentative {i+1}: {loc}")
            button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(loc))
            button_text = button.text or button.get_attribute("value") or "sans-texte"
            logging.info(f"  Bouton trouvé: '{button_text}'")
            
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
            time.sleep(1)
            button.click()
            logging.info(f"✅ Clic réussi sur le bouton (méthode {i+1})")
            button_clicked = True
            break
            
        except TimeoutException:
            logging.info(f"  ❌ Méthode {i+1} échouée: timeout")
            continue
        except Exception as e:
            logging.info(f"  ❌ Méthode {i+1} échouée: {e}")
            continue
    
    if not button_clicked:
        # Diagnostic final: lister tous les boutons
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            logging.error(f"Diagnostic: {len(all_buttons)} boutons trouvés sur la page:")
            for i, btn in enumerate(all_buttons[:10]):  # Limiter à 10 pour éviter le spam
                btn_text = btn.text or btn.get_attribute("value") or "sans-texte"
                btn_id = btn.get_attribute("id") or "sans-id"
                logging.error(f"  Bouton {i+1}: id='{btn_id}', texte='{btn_text}'")
        except Exception as diag_error:
            logging.error(f"Erreur lors du diagnostic des boutons: {diag_error}")
        
        raise TimeoutException("Impossible de cliquer sur le bouton de préparation.")

    # 2) Attendre la modale de progression
    logging.info("⏳ Attente de la modale de progression...")
    modal_found = False
    for wait_time in [30, 60, 90]:
        try:
            progress_modal = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.ID, "download-progress"))
            )
            if progress_modal.is_displayed():
                logging.info("✅ Modale de progression trouvée et visible")
                modal_found = True
                break
            else:
                logging.info("⚠️ Modale trouvée mais pas visible, attente...")
                time.sleep(5)
        except TimeoutException:
            logging.warning(f"⏳ Modale non trouvée après {wait_time}s, continue...")
            continue
    
    if not modal_found:
        logging.warning("⚠️ Modale de progression non trouvée, tentative de continuer...")

    # 3) Recherche du lien de téléchargement
    logging.info("🔗 Recherche du lien de téléchargement...")
    link_locators = [
        (By.CSS_SELECTOR, "#download-progress form a"),
        (By.XPATH, "//div[@id='download-progress']//form//a"),
        (By.XPATH, "//div[@id='download-progress']//a[contains(., 'Download')]"),
        (By.XPATH, "//a[contains(text(), 'Download') or contains(@href, 'download')]"),
        (By.CSS_SELECTOR, "a[href*='download']"),
    ]
    
    link_clicked = False
    max_wait_for_link = 240  # 4 minutes
    start_wait = time.time()
    
    while time.time() - start_wait < max_wait_for_link and not link_clicked:
        for i, loc in enumerate(link_locators):
            try:
                logging.info(f"  Recherche lien méthode {i+1}...")
                link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(loc))
                
                if link.is_displayed() and link.is_enabled():
                    link_text = link.text or link.get_attribute("href") or "sans-texte"
                    logging.info(f"  Lien trouvé: '{link_text}'")
                    
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                    time.sleep(1)
                    
                    try:
                        link.click()
                        logging.info(f"✅ Clic sur le lien réussi (méthode {i+1})")
                    except StaleElementReferenceException:
                        link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(loc))
                        link.click()
                        logging.info(f"✅ Clic sur le lien réussi après re-recherche (méthode {i+1})")
                    
                    link_clicked = True
                    break
                    
            except TimeoutException:
                continue
            except Exception as e:
                logging.warning(f"  Erreur méthode {i+1}: {e}")
                continue
        
        if not link_clicked:
            logging.info("⏳ Lien non trouvé, attente de 10 secondes...")
            time.sleep(10)
    
    if not link_clicked:
        # Diagnostic final: chercher tous les liens
        try:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            logging.error(f"Diagnostic: {len(all_links)} liens trouvés:")
            for i, link in enumerate(all_links[:15]):  # Limiter à 15
                link_text = link.text or "sans-texte"
                link_href = link.get_attribute("href") or "sans-href"
                if "download" in link_text.lower() or "download" in link_href.lower():
                    logging.error(f"  Lien {i+1} (potentiel): '{link_text}' -> {link_href}")
        except Exception as diag_error:
            logging.error(f"Erreur lors du diagnostic des liens: {diag_error}")
        
        raise TimeoutException("Lien de téléchargement non trouvé ou non cliquable.")

    # 4) Attendre la fin du téléchargement
    logging.info("📥 Attente de la fin du téléchargement...")
    try:
        fpath = wait_for_download_complete(DOWNLOAD_DIR, before, timeout=900)  # 15 minutes
        logging.info(f"✅ Téléchargement terminé: {fpath}")
        return fpath
    except Exception as e:
        logging.error(f"❌ Erreur pendant l'attente du téléchargement: {e}")
        
        # Vérifier s'il y a quand même de nouveaux fichiers
        after_files = list_files(DOWNLOAD_DIR)
        new_files = after_files - before
        if new_files:
            xlsx_files = [f for f in new_files if f.lower().endswith('.xlsx')]
            if xlsx_files:
                latest = max(
                    (os.path.join(DOWNLOAD_DIR, f) for f in xlsx_files),
                    key=lambda p: os.path.getmtime(p),
                )
                logging.info(f"🔍 Fichier trouvé malgré l'erreur: {os.path.basename(latest)}")
                return latest
        
        raise


# =========================
# UTILITAIRES POUR VÉRIFICATION DES FICHIERS
# =========================
def normalize_filename(name: str) -> str:
    """Normalise un nom de fichier pour la comparaison"""
    return re.sub(r'[^a-zA-Z0-9]', '', name.lower())


def check_file_exists_today(export_item: dict, download_dir: str) -> tuple:
    """
    Vérifie si un fichier existe déjà pour cet export avec la date d'aujourd'hui
    
    Args:
        export_item: Dictionnaire avec 'name' et optionnellement 'pattern'
        download_dir: Répertoire de téléchargement
    
    Returns:
        (existe: bool, chemin_fichier: str, raison: str)
    """
    name = export_item["name"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
            return False, "", f"Répertoire de téléchargement créé: {download_dir}"
        
        # Obtenir tous les fichiers .xlsx du répertoire
        all_files = [f for f in os.listdir(download_dir) if f.lower().endswith('.xlsx')]
        
        if not all_files:
            return False, "", f"Aucun fichier Excel trouvé dans {download_dir}"
        
        # Créer des mots-clés à partir du nom
        keywords = [word.lower() for word in re.findall(r'[a-zA-Z0-9]+', name) if len(word) > 2]
        
        # Fichiers candidats pour cet export
        candidate_files = []
        
        for file in all_files:
            file_path = os.path.join(download_dir, file)
            file_normalized = normalize_filename(file)
            
            # Vérifier la date de création ET modification
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            file_creation_date = file_creation_time.strftime("%Y-%m-%d")
            file_modification_date = file_modification_time.strftime("%Y-%m-%d")
            
            # Fichier d'aujourd'hui
            is_today_file = (file_creation_date == today) or (file_modification_date == today)
            
            if is_today_file:
                # Vérifier si le fichier correspond aux mots-clés
                match_count = sum(1 for keyword in keywords if keyword in file_normalized)
                
                # Exiger au moins 1 correspondance ou 50% des mots-clés
                min_matches = max(1, len(keywords) // 2) if len(keywords) > 0 else 0
                
                if match_count >= min_matches:
                    candidate_files.append({
                        'path': file_path,
                        'name': file,
                        'creation_date': file_creation_date,
                        'modification_date': file_modification_date,
                        'creation_time': file_creation_time,
                        'modification_time': file_modification_time,
                        'match_count': match_count,
                        'file_size': os.path.getsize(file_path)
                    })
        
        if not candidate_files:
            return False, "", f"Aucun fichier d'aujourd'hui trouvé pour '{name}'"
        
        # Prendre le fichier avec le plus de correspondances, puis le plus récent
        best_file = max(candidate_files, key=lambda f: (f['match_count'], f['modification_time']))
        
        return True, best_file['path'], f"Fichier d'aujourd'hui trouvé: {best_file['name']} (créé: {best_file['creation_date']}, modifié: {best_file['modification_date']}, taille: {best_file['file_size']:,} bytes)"
            
    except Exception as e:
        logging.error(f"Erreur lors de la vérification de '{name}': {e}")
        return False, "", f"Erreur: {e}"


def verify_download_success(export_item: dict, download_dir: str, downloaded_file_path: str) -> tuple:
    """
    Vérifie qu'un fichier téléchargé correspond bien à l'export demandé
    
    Args:
        export_item: Dictionnaire avec les informations de l'export
        download_dir: Répertoire de téléchargement
        downloaded_file_path: Chemin du fichier téléchargé
    
    Returns:
        (succès: bool, message: str)
    """
    try:
        if not downloaded_file_path:
            return False, "Aucun chemin de fichier fourni"
            
        if not os.path.exists(downloaded_file_path):
            return False, f"Fichier téléchargé non trouvé: {downloaded_file_path}"
        
        # Vérifier que c'est un fichier Excel valide
        if not downloaded_file_path.lower().endswith('.xlsx'):
            return False, f"Le fichier téléchargé n'est pas un fichier Excel: {os.path.basename(downloaded_file_path)}"
        
        # Vérifier la taille du fichier (doit être > 1KB pour être valide)
        file_size = os.path.getsize(downloaded_file_path)
        if file_size == 0:
            return False, f"Le fichier téléchargé est vide: {os.path.basename(downloaded_file_path)}"
        elif file_size < 1024:  # Moins de 1KB est suspect
            return False, f"Le fichier téléchargé est trop petit ({file_size} bytes): {os.path.basename(downloaded_file_path)}"
        
        # Vérifier que le fichier peut être ouvert (test de corruption)
        try:
            # Test d'ouverture basique
            with open(downloaded_file_path, 'rb') as f:
                # Lire les premiers bytes pour vérifier la signature Excel
                header = f.read(8)
                if not header.startswith(b'PK'):  # Signature ZIP (Excel est un ZIP)
                    return False, f"Le fichier ne semble pas être un fichier Excel valide (signature incorrecte)"
            
            # Test de lecture avec pandas
            try:
                df_test = pd.read_excel(downloaded_file_path, nrows=5)
                row_count = len(df_test)
                col_count = len(df_test.columns)
                
                if row_count == 0 and col_count == 0:
                    return False, f"Le fichier Excel est vide (aucune donnée)"
                
                logging.info(f"Fichier Excel vérifié: {row_count} lignes, {col_count} colonnes détectées")
                
            except Exception as pandas_error:
                return False, f"Le fichier Excel semble corrompu: {pandas_error}"
        
        except Exception as file_error:
            return False, f"Erreur lors de la lecture du fichier: {file_error}"
        
        # Vérifier la date de création (doit être récente)
        file_creation_time = datetime.fromtimestamp(os.path.getctime(downloaded_file_path))
        file_age = datetime.now() - file_creation_time
        
        return True, f"Téléchargement vérifié avec succès: {os.path.basename(downloaded_file_path)} ({file_size:,} bytes, créé: {file_creation_time.strftime('%H:%M:%S')})"
        
    except Exception as e:
        return False, f"Erreur lors de la vérification: {e}"


# =========================
# MAIN SIMPLIFIÉ POUR DEBUG
# =========================
def main():
    load_dotenv(ENV_FILE)
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD") or os.getenv("PASSWORD_CC")

    if not email or not password:
        raise RuntimeError(f"EMAIL / PASSWORD introuvables dans {ENV_FILE}")

    logging.info(f"🔐 Authentification avec: {email}")
    logging.info(f"📁 Répertoire de téléchargement: {DOWNLOAD_DIR}")

    driver = setup_driver(DOWNLOAD_DIR)

    try:
        # Test avec UN SEUL export pour commencer
        test_export = EXPORTS[0]  # Premier export seulement
        logging.info(f"🧪 TEST avec un seul export: {test_export['name']}")
        
        # Login
        logging.info("� Tentative de connexion...")
        commcare_login(driver, email, password, test_export["url"])
        
        # État avant téléchargement
        before_files = list_files(DOWNLOAD_DIR)
        logging.info(f"📄 Fichiers avant: {len(before_files)} fichiers")
        
        # Tentative de téléchargement avec diagnostic complet
        logging.info("📥 Démarrage du téléchargement...")
        try:
            path = trigger_and_download(driver, test_export["url"])
            
            if path and os.path.isfile(path):
                file_size = os.path.getsize(path)
                logging.info(f"🎉 SUCCÈS! Fichier téléchargé: {os.path.basename(path)} ({file_size:,} bytes)")
                
                # Vérification finale
                after_files = list_files(DOWNLOAD_DIR)
                logging.info(f"📄 Fichiers après: {len(after_files)} fichiers")
                new_files = after_files - before_files
                if new_files:
                    logging.info(f"✅ Nouveaux fichiers détectés: {list(new_files)}")
                else:
                    logging.warning("⚠️ Aucun nouveau fichier détecté dans le répertoire")
                    
            else:
                logging.error(f"❌ Échec: Aucun fichier valide retourné (path={path})")
                
        except Exception as download_error:
            logging.error(f"❌ Erreur lors du téléchargement: {download_error}")
            
            # Diagnostic post-erreur
            after_files = list_files(DOWNLOAD_DIR)
            logging.info(f"📄 Fichiers après erreur: {len(after_files)} fichiers")
            if after_files:
                logging.info(f"📋 Fichiers présents: {list(after_files)}")
            
            # Vérifier l'état du navigateur
            try:
                current_url = driver.current_url
                page_title = driver.title
                logging.info(f"🌐 URL actuelle: {current_url}")
                logging.info(f"📰 Titre de la page: {page_title}")
            except Exception as browser_error:
                logging.error(f"❌ Erreur lors de l'inspection du navigateur: {browser_error}")
            
            raise

    except Exception as main_error:
        logging.error(f"❌ Erreur principale: {main_error}")
        raise
    finally:
        logging.info("🔒 Fermeture du navigateur...")
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()

    # Exemple de vérif simple (si vous avez des noms attendus)
    # today_date = datetime.today().strftime('%Y-%m-%d')
    # expected = [
    #     f"Caris Health Agent - Enfant - Ration et autres visites (created 2022-08-29) {today_date}.xlsx",
    # ]
    # check_files(expected)

# =========================
# FONCTION POUR LE NOTEBOOK
# =========================
def download_files():
    """
    Fonction wrapper pour le notebook - appelle main() avec gestion d'erreurs améliorée
    """
    main()
