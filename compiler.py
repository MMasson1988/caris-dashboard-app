# -*- coding: utf-8 -*-
"""
CommCare Smart Downloader - Version corrigée avec logique de function.py
"""

import os
import re
import time
import glob
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

# ===================== CONFIG =====================
DOWNLOAD_DIR = r"C:\Users\Moise\Downloads\caris-dashboard-app\data"

# Liste des bases (sans date ni extension)
EXPECTED_BASES = [
    "Caris Health Agent - Enfant - Visite Enfant",
    "Caris Health Agent - Enfant - APPELS OEV", 
    "Caris Health Agent - Femme PMTE  - Visite PTME",
    "Caris Health Agent - Femme PMTE  - Ration & Autres Visites",
    "Caris Health Agent - Enfant - Ration et autres visites",
    "Caris Health Agent - Femme PMTE  - APPELS PTME",
]

# Mapping des bases vers les URLs CommCare
EXPORT_URLS = {
    "Caris Health Agent - Enfant - Visite Enfant": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/7d960d6c03d9d6c35a8d083c288e7c8d/",
    "Caris Health Agent - Enfant - APPELS OEV": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/f817d728df7d0070b29160e54a22765b/",
    "Caris Health Agent - Femme PMTE  - Visite PTME": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/4fde80e15e96e8214eb58d5761049f0f/",
    "Caris Health Agent - Femme PMTE  - Ration & Autres Visites": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c5c5e2292ad223156f72620c6e0fd99f/",
    "Caris Health Agent - Enfant - Ration et autres visites": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/bc95b54ff93a6c62c22a2e2f17852a90/",
    "Caris Health Agent - Femme PMTE  - APPELS PTME": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c1a3280f5e34a2b6078439f9b59ad72c/",
}

# Alias pratique attendu par d'autres scripts: expose la même table d'URLs
export_plus = EXPORT_URLS

# Retries & timeouts
MAX_RETRIES_PER_FILE = 3
MAX_GLOBAL_PASSES = 3
VERIFICATION_TIMEOUT = 60
HEADLESS = False

# ===================== LOGGING =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("commcare-downloader")

# ===================== UTILS =====================
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def expected_filename_for_today(base: str, sep: str = " ") -> str:
    return f"{base}{sep}(created XXXX-XX-XX) {today_str()}.xlsx"

def list_xlsx(folder: str) -> List[str]:
    return [os.path.basename(p) for p in glob.glob(os.path.join(folder, "*.xlsx"))]

def list_partial_downloads(folder: str) -> List[str]:
    return glob.glob(os.path.join(folder, "*.crdownload"))

def cleanup_orphan_crdownload(folder: str) -> None:
    for p in list_partial_downloads(folder):
        try:
            os.remove(p)
        except Exception:
            pass

def human_list(items: List[str]) -> str:
    return "[" + ", ".join(items) + "]" if items else "[]"

# ===================== PATTERN =====================
def build_pattern_with_today(base: str) -> re.Pattern:
    date = today_str()
    base_esc = re.escape(base)
    # Autorise un suffixe " (n)" avant l'extension pour les duplications Windows
    pat = rf"^{base_esc}\s*\(created\s+\d{{4}}-\d{{2}}-\d{{2}}\)\s+{re.escape(date)}(?:\s+\(\d+\))?\.xlsx$"
    return re.compile(pat, re.IGNORECASE)

def file_matches_today(base: str, filename: str) -> bool:
    return bool(build_pattern_with_today(base).match(filename))

# ===================== VERIFICATION =====================
def check_existing_files(expected_bases: List[str], folder_path: str) -> Tuple[List[str], Dict[str, List[str]]]:
    ensure_dir(folder_path)
    present = list_xlsx(folder_path)
    present_map: Dict[str, List[str]] = {}
    missing_bases: List[str] = []

    for base in expected_bases:
        matches = [f for f in present if file_matches_today(base, f)]
        present_map[base] = matches
        if not matches:
            missing_bases.append(base)

    return missing_bases, present_map

def _file_size_stable(path: str, wait_interval: float = 1.5) -> bool:
    try:
        s1 = os.path.getsize(path)
        time.sleep(wait_interval)
        s2 = os.path.getsize(path)
        return s1 > 0 and s1 == s2
    except Exception:
        return False

def verify_download_success_for_base(base: str, folder_path: str, timeout: int = VERIFICATION_TIMEOUT) -> Optional[str]:
    pat = build_pattern_with_today(base)
    end = time.time() + timeout

    while time.time() < end:
        if list_partial_downloads(folder_path):
            time.sleep(1.0)

        for f in list_xlsx(folder_path):
            if pat.match(f):
                full = os.path.join(folder_path, f)
                if _file_size_stable(full):
                    return full
        time.sleep(1.0)

    return None

# ===================== SELENIUM =====================
def unfreeze_interface(driver):
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        driver.execute_script("arguments[0].click();", body)
        time.sleep(0.5)
        
        actions = ActionChains(driver)
        actions.move_by_offset(50, 50).click().perform()
        time.sleep(0.3)
        actions.move_by_offset(-50, -50).perform()
        
        body.send_keys(Keys.ESCAPE)
        time.sleep(0.5)
            
    except Exception as e:
        log.warning(f"Erreur lors du deblocage de l'interface : {e}")

def set_date_range(driver, start_date="2025-01-01", end_date="2025-08-13"):
    try:
        date_input = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, "id_date_range"))
        )
        
        date_input.click()
        time.sleep(0.5)
        
        date_input.clear()
        time.sleep(0.5)
        
        date_input.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        date_input.send_keys(Keys.DELETE)
        time.sleep(0.5)
        
        date_range_value = f"{start_date} to {end_date}"
        date_input.send_keys(date_range_value)
        
        log.info(f"Plage de dates saisie : {date_range_value}")
        
        date_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        unfreeze_interface(driver)
        time.sleep(2)
        
    except Exception as e:
        log.warning(f"Erreur lors de la definition de la plage de dates : {e}")
        try:
            unfreeze_interface(driver)
        except:
            pass

def trigger_download(export_base: str, driver) -> None:
    if export_base not in EXPORT_URLS:
        log.error(f"URL non trouvee pour l'export : {export_base}")
        return
        
    export_url = EXPORT_URLS[export_base]
    log.info(f"Acces a l'URL d'export : {export_url}")
    
    try:
        driver.get(export_url)
        time.sleep(3)
        
        set_date_range(driver, "2025-01-01", "2025-08-13")
        time.sleep(2)
        
        # Bouton Prepare/Download
        prepare_locators = [
            (By.CSS_SELECTOR, "#download-export-form button[type='submit']"),
            (By.CSS_SELECTOR, "#download-export-form .btn-primary"),
            (By.XPATH, "//div[@id='download-export-form']//button[contains(@class,'btn')]"),
        ]
        clicked = False
        for loc in prepare_locators:
            try:
                btn = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(loc))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                btn.click()
                clicked = True
                break
            except TimeoutException:
                continue
        
        if not clicked:
            raise TimeoutException("Bouton de preparation introuvable.")
        
        # Attendre la modale
        try:
            WebDriverWait(driver, 90).until(
                EC.visibility_of_element_located((By.ID, "download-progress"))
            )
        except TimeoutException:
            pass
        
        # Lien Download
        link_locators = [
            (By.CSS_SELECTOR, "#download-progress form a"),
            (By.XPATH, "//div[@id='download-progress']//form//a"),
            (By.XPATH, "//div[@id='download-progress']//a[contains(., 'Download')]"),
        ]
        link_clicked = False
        for loc in link_locators:
            try:
                a = WebDriverWait(driver, 120).until(EC.element_to_be_clickable(loc))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", a)
                try:
                    a.click()
                except StaleElementReferenceException:
                    a = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(loc))
                    a.click()
                link_clicked = True
                break
            except TimeoutException:
                continue
        
        if not link_clicked:
            raise TimeoutException("Lien de telechargement non trouve dans la modale.")
            
        log.info(f"Telechargement declenche pour {export_base}")
        
    except Exception as e:
        log.error(f"Erreur lors du declenchement du telechargement pour {export_base}: {e}")
        raise

def download_with_verification(export_base: str, driver, max_retries: int = MAX_RETRIES_PER_FILE) -> bool:
    target_hint = expected_filename_for_today(export_base)

    for attempt in range(1, max_retries + 1):
        # Vérification préventive: sauter si déjà présent
        if any(file_matches_today(export_base, f) for f in list_xlsx(DOWNLOAD_DIR)):
            log.info(f"Deja present pour {export_base} (avant tentative {attempt}). Aucun telechargement lance.")
            return True
        log.info(f"Telechargement de {target_hint} (tentative {attempt}/{max_retries})...")
        cleanup_orphan_crdownload(DOWNLOAD_DIR)

        try:
            trigger_download(export_base, driver)
        except Exception as e:
            log.error(f"Erreur pendant le declenchement du telechargement pour {export_base}: {e}")

        path = verify_download_success_for_base(export_base, DOWNLOAD_DIR, timeout=VERIFICATION_TIMEOUT)
        if path:
            log.info("Telechargement verifie avec succes: %s", os.path.basename(path))
            return True

        log.warning("Non confirme pour %s (tentative %d)", target_hint, attempt)
        cleanup_orphan_crdownload(DOWNLOAD_DIR)

    log.error("Echec apres %d tentatives pour %s", max_retries, target_hint)
    return False

def start_chrome(download_dir: str, headless: bool = HEADLESS):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def commcare_login(driver, email: str, password: str, first_export_url: str):
    driver.get(first_export_url)

    user = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.ID, "id_auth-username"))
    )
    pwd = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.ID, "id_auth-password"))
    )

    user.clear()
    user.send_keys(email.strip())
    pwd.clear()
    pwd.send_keys(password.strip())

    login_btn = driver.find_element(
        By.XPATH,
        "//form[.//input[@id='id_auth-username']]//button[@type='submit']"
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_btn)
    login_btn.click()

    try:
        WebDriverWait(driver, 2).until(lambda d: "/login" not in d.current_url)
    except Exception:
        pwd.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 30).until(
            lambda d: ("/login" not in d.current_url) or bool(d.find_elements(By.ID, "download-export-form"))
        )
        log.info("Authentification reussie.")
    except TimeoutException:
        raise RuntimeError("Echec d'authentification")

# ===================== MAIN =====================
def main_enhanced(driver=None):
    from dotenv import load_dotenv
    
    t0 = time.time()
    ensure_dir(DOWNLOAD_DIR)

    log.info("=== VERIFICATION INITIALE ===")
    log.info("Dossier: %s", DOWNLOAD_DIR)
    log.info("Fichiers attendus (bases): %d", len(EXPECTED_BASES))

    missing_bases, present_map = check_existing_files(EXPECTED_BASES, DOWNLOAD_DIR)
    nb_present = sum(1 for v in present_map.values() if v)

    log.info("Presents (aujourd'hui): %d", nb_present)
    log.info("Manquants (aujourd'hui): %d", len(missing_bases))
    if missing_bases:
        to_dl_list = [expected_filename_for_today(b) for b in missing_bases]
        log.info("A telecharger: %s", human_list(to_dl_list))
    else:
        log.info("Tous les fichiers dates %s sont deja presents. Rien a faire.", today_str())
        return

    own_driver = False
    if driver is None:
        driver = start_chrome(DOWNLOAD_DIR, headless=HEADLESS)
        own_driver = True

    try:
        # Login si nécessaire
        if missing_bases:
            load_dotenv("id_cc.env")
            email = os.getenv("EMAIL")
            password = os.getenv("PASSWORD") or os.getenv("PASSWORD_CC")
            
            if not email or not password:
                raise RuntimeError("EMAIL / PASSWORD introuvables dans id_cc.env")
            
            first_url = EXPORT_URLS[missing_bases[0]]
            commcare_login(driver, email, password, first_url)

        # Passes globales
        total_success = 0
        files_to_download = missing_bases[:]
        current_pass = 1

        while files_to_download and current_pass <= MAX_GLOBAL_PASSES:
            log.info("=== PASSE %d ===", current_pass)
            successful_downloads = 0
            failed_files: List[str] = []

            for base in files_to_download:
                # Sécurité: ne rien tenter si déjà présent
                if any(file_matches_today(base, f) for f in list_xlsx(DOWNLOAD_DIR)):
                    log.info(f"Deja present pour {base}. Aucun telechargement lance.")
                    successful_downloads += 1
                    continue

                ok = download_with_verification(base, driver, max_retries=MAX_RETRIES_PER_FILE)
                if ok:
                    successful_downloads += 1
                else:
                    failed_files.append(base)

            log.info("Resultats Passe %d:", current_pass)
            log.info("   Reussis: %d", successful_downloads)
            log.info("   Echoues: %d", len(failed_files))
            if failed_files:
                ff_disp = [expected_filename_for_today(b) for b in failed_files]
                log.info("   Fichiers echoues: %s", human_list(ff_disp))

            total_success += successful_downloads
            files_to_download = failed_files
            current_pass += 1

        # Rapport final
        dt = time.time() - t0
        total_failed = len(files_to_download)

        log.info("=== RAPPORT FINAL ===")
        if total_failed == 0 and total_success > 0:
            log.info("Tous les telechargements (dates %s) termines !", today_str())
        else:
            log.warning("Telechargements incomplets pour la date %s.", today_str())

        log.info("Total reussis: %d", total_success)
        log.info("Total echoues: %d", total_failed)
        log.info("Temps total: %dm %ds", int(dt // 60), int(dt % 60))

    finally:
        if own_driver and driver:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main_enhanced()
