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
    "muso_groupes",
    "muso_beneficiaries",
    "Household mother",
    "Ajout de menages ptme [officiel]",
    "PTME WITH PATIENT CODE",
    "household_child",
    "All_child_PatientCode_CaseID",  
]

# Mapping des bases vers les URLs CommCare
EXPORT_URLS = {
    "Caris Health Agent - Enfant - Visite Enfant": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/7d960d6c03d9d6c35a8d083c288e7c8d/",
    "Caris Health Agent - Enfant - APPELS OEV": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/f817d728df7d0070b29160e54a22765b/",
    "Caris Health Agent - Femme PMTE  - Visite PTME": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/4fde80e15e96e8214eb58d5761049f0f/",
    "Caris Health Agent - Femme PMTE  - Ration & Autres Visites": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c5c5e2292ad223156f72620c6e0fd99f/",
    "Caris Health Agent - Enfant - Ration et autres visites": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/bc95b54ff93a6c62c22a2e2f17852a90/",
    "Caris Health Agent - Femme PMTE  - APPELS PTME": "https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/c1a3280f5e34a2b6078439f9b59ad72c/",
    "Household mother":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/3eb9f92d8d82501ebe5c8cb89b83dbba/",
    "Ajout de menages ptme [officiel]":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/form/download/269567f0b84da5a1767712e519ced62e/",
    "PTME WITH PATIENT CODE":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/af6c4186011182dfda68a84536231f68/",
    "household_child":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/f6ddce2133f8d233d9fbd9341220ed6f/",
    "All_child_PatientCode_CaseID":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/0379abcdafdf9979863c2d634792b5a8/",
    "muso_groupes":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/462626788779f3781f9b9ebcce200225/",
    "muso_beneficiaries":"https://www.commcarehq.org/a/caris-test/data/export/custom/new/case/download/f831c9c92760a38d24b3829df5621d20/",
}

# Retries & timeouts
MAX_RETRIES_PER_FILE = 3
MAX_GLOBAL_PASSES = 3
VERIFICATION_TIMEOUT = 60
HEAVY_FILE_TIMEOUT = 180  # 3 minutes pour les gros fichiers
HEADLESS = False

# Fichiers lourds nécessitant plus de temps
HEAVY_FILES = [
    "muso_beneficiaries"
]

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
    # Nom attendu spécial pour "Household mother"
    if base.lower() == "household mother":
        return f"household mother {today_str()}.xlsx"
    else:
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

def cleanup_duplicate_files(folder: str) -> None:
    """Nettoie les fichiers dupliqués en gardant le plus récent"""
    ensure_dir(folder)
    files = list_xlsx(folder)
    
    # Grouper les fichiers par base
    file_groups = {}
    for filename in files:
        # Identifier la base du fichier
        for base in EXPECTED_BASES:
            if file_matches_today(base, filename):
                if base not in file_groups:
                    file_groups[base] = []
                file_groups[base].append(filename)
                break
    
    # Pour chaque groupe, garder seulement le plus récent
    for base, group_files in file_groups.items():
        if len(group_files) > 1:
            log.info(f"Fichiers dupliqués trouvés pour {base}: {group_files}")
            
            # Trier par date de modification (plus récent en dernier)
            group_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)))
            
            # Garder le plus récent, supprimer les autres
            files_to_delete = group_files[:-1]
            for file_to_delete in files_to_delete:
                try:
                    file_path = os.path.join(folder, file_to_delete)
                    os.remove(file_path)
                    log.info(f"Fichier dupliqué supprimé: {file_to_delete}")
                except Exception as e:
                    log.warning(f"Impossible de supprimer {file_to_delete}: {e}")

def human_list(items: List[str]) -> str:
    return "[" + ", ".join(items) + "]" if items else "[]"

# ===================== PATTERN =====================
def build_pattern_with_today(base: str) -> re.Pattern:
    date = today_str()
    base_esc = re.escape(base)
    
    # Fichiers avec pattern simplifié (sans "(created XXXX-XX-XX)")
    # Tous en minuscules pour la comparaison
    simple_pattern_files = [
        "household mother",
        "ajout de menages ptme [officiel]",
        "ptme with patient code",
        "household_child",
        "all_child_patientcode_caseid"
    ]
    
    # Fichiers avec pattern spécial (ont "(created XXXX-XX-XX)" mais avec une date fixe)
    special_pattern_files = {
        "muso_groupes": r"muso_groupes\s*\(created\s+2025-03-25\)\s+",
        "muso_beneficiaries": r"muso_beneficiaries\s*\(created\s+2025-03-25\)\s+"
    }
    
    if base.lower() in simple_pattern_files:
        # Pattern simplifié: Base 2025-08-13.xlsx ou Base 2025-08-13 (1).xlsx
        pat = rf"^{base_esc}\s+{re.escape(date)}(?:\s+\(\d+\))?\.xlsx$"
    elif base in special_pattern_files:
        # Pattern spécial avec date de création fixe
        special_prefix = special_pattern_files[base]
        pat = rf"^{special_prefix}{re.escape(date)}(?:\s+\(\d+\))?\.xlsx$"
    else:
        # Pattern normal: Base (created XXXX-XX-XX) YYYY-MM-DD.xlsx
        pat = rf"^{base_esc}\s*\(created\s+\d{{4}}-\d{{2}}-\d{{2}}\)\s+{re.escape(date)}\.xlsx$"
    
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
    # Utiliser un timeout plus long pour les fichiers lourds
    actual_timeout = HEAVY_FILE_TIMEOUT if base in HEAVY_FILES else timeout
    log.info(f"Vérification du téléchargement pour {base} (timeout: {actual_timeout}s)")
    
    pat = build_pattern_with_today(base)
    end = time.time() + actual_timeout

    while time.time() < end:
        if list_partial_downloads(folder_path):
            log.info(f"Téléchargement en cours pour {base}...")
            time.sleep(2.0)  # Attendre plus longtemps pour les gros fichiers

        for f in list_xlsx(folder_path):
            if pat.match(f):
                full = os.path.join(folder_path, f)
                if _file_size_stable(full, wait_interval=2.0):  # Plus d'attente pour la stabilité
                    return full
        time.sleep(2.0)  # Vérifier moins fréquemment

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

def set_date_range(driver, start_date="2021-01-01", end_date="2025-08-13"):
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
    
    # Timeout spécial pour les gros fichiers
    is_heavy_file = export_base in HEAVY_FILES
    preparation_timeout = 300 if is_heavy_file else 180  # 5 min pour les gros, 3 min pour les autres
    log.info(f"Timeout de préparation: {preparation_timeout}s ({'GROS FICHIER' if is_heavy_file else 'fichier normal'})")
    
    try:
        driver.get(export_url)
        time.sleep(3)
        
        set_date_range(driver, "2021-01-01", "2025-08-13")
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
        
        # Attendre la modale et la génération du fichier
        try:
            log.info("Attente de l'apparition de la modale de téléchargement...")
            WebDriverWait(driver, 120).until(  # Augmenté à 2 minutes
                EC.visibility_of_element_located((By.ID, "download-progress"))
            )
            log.info("Modale de téléchargement apparue, attente de la génération du fichier...")
            
            # Attendre beaucoup plus longtemps pour la génération du fichier
            # Certains exports peuvent prendre plusieurs minutes à générer
            base_wait = 60 if is_heavy_file else 30  # 1 min pour gros fichiers, 30s pour autres
            time.sleep(base_wait)
            log.info(f"Attente de base terminée ({base_wait}s)")
            
            # Attendre spécifiquement que le lien de téléchargement apparaisse
            log.info("Recherche du lien de téléchargement dans la modale...")
            try:
                # Attendre qu'un lien de téléchargement soit disponible
                WebDriverWait(driver, preparation_timeout).until(  # Timeout adapté au type de fichier
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#download-progress a, #download-progress form a"))
                )
                log.info("✅ Lien de téléchargement détecté dans la modale!")
                
                # Attendre encore un peu pour s'assurer que le lien est entièrement chargé
                final_wait = 15 if is_heavy_file else 10
                time.sleep(final_wait)
                log.info(f"Attente finale terminée ({final_wait}s)")
                
            except TimeoutException:
                log.warning(f"⚠️ Timeout ({preparation_timeout}s) lors de l'attente du lien de téléchargement, tentative de recherche manuelle...")
                # Continuer quand même avec la recherche manuelle
                
        except TimeoutException:
            log.warning("⚠️ Timeout lors de l'attente de la modale, tentative de recherche manuelle...")
            # Continuer quand même
        
        # Lien Download - Version ultra-robuste avec stratégies multiples
        link_locators = [
            # Sélecteurs spécifiques pour la modale de download
            (By.CSS_SELECTOR, "#download-progress form a"),
            (By.CSS_SELECTOR, "#download-progress a"),
            (By.XPATH, "//div[@id='download-progress']//form//a"),
            (By.XPATH, "//div[@id='download-progress']//a[contains(., 'Download')]"),
            (By.XPATH, "//div[@id='download-progress']//a[contains(@href, '.xlsx')]"),
            # Sélecteurs plus généraux
            (By.XPATH, "//a[contains(text(), 'Download')]"),
            (By.XPATH, "//a[contains(@href, 'download')]"),
            (By.CSS_SELECTOR, "a[href*='download']"),
            # Sélecteurs pour boutons de download
            (By.XPATH, "//button[contains(text(), 'Download')]"),
            (By.CSS_SELECTOR, "button[title*='Download']"),
        ]
        
        link_clicked = False
        
        # Attendre que la modale soit complètement chargée
        log.info("Attente supplémentaire pour le chargement complet...")
        time.sleep(15)  # Augmenté de 5 à 15 secondes
        
        # Stratégie 1: Recherche avec tous les sélecteurs
        for i, loc in enumerate(link_locators):
            try:
                log.info(f"Tentative {i+1}: Recherche du lien de téléchargement...")
                
                # Attendre que l'élément soit cliquable avec timeout encore plus long
                a = WebDriverWait(driver, 120).until(EC.element_to_be_clickable(loc))  # Augmenté à 2 minutes
                
                # Vérifier que l'élément est visible
                if not a.is_displayed():
                    log.warning(f"Élément trouvé mais non visible avec le sélecteur {i+1}")
                    continue
                
                # Log des informations de l'élément trouvé
                href = a.get_attribute('href')
                text = a.text.strip()
                log.info(f"Élément trouvé - Href: {href}, Texte: '{text}'")
                
                # Stratégies de clic multiples avec vérifications
                click_success = False
                
                # Méthode 1: Scroll et clic JavaScript
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", a)
                    time.sleep(2)
                    
                    # Vérifier que l'élément est toujours valide
                    if a.is_displayed() and a.is_enabled():
                        driver.execute_script("arguments[0].click();", a)
                        log.info(f"✅ Clic JavaScript réussi avec le sélecteur {i+1}")
                        click_success = True
                    else:
                        log.warning(f"Élément non cliquable après scroll")
                except Exception as e:
                    log.warning(f"Clic JavaScript échoué: {e}")
                
                # Méthode 2: ActionChains avec hover puis clic
                if not click_success:
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element(a).pause(1).click(a).perform()
                        log.info(f"✅ Clic ActionChains réussi avec le sélecteur {i+1}")
                        click_success = True
                    except Exception as e:
                        log.warning(f"Clic ActionChains échoué: {e}")
                
                # Méthode 3: Clic Selenium normal après attente
                if not click_success:
                    try:
                        time.sleep(1)
                        a.click()
                        log.info(f"✅ Clic Selenium réussi avec le sélecteur {i+1}")
                        click_success = True
                    except StaleElementReferenceException:
                        log.warning("Élément devenu obsolète, re-recherche...")
                        try:
                            a = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(loc))
                            a.click()
                            log.info(f"✅ Clic après re-recherche réussi avec le sélecteur {i+1}")
                            click_success = True
                        except Exception as e:
                            log.warning(f"Re-recherche échouée: {e}")
                    except Exception as e:
                        log.warning(f"Clic Selenium échoué: {e}")
                
                # Méthode 4: Simulation de touches Enter/Space
                if not click_success:
                    try:
                        a.send_keys(Keys.RETURN)
                        log.info(f"✅ Simulation ENTER réussie avec le sélecteur {i+1}")
                        click_success = True
                    except Exception as e:
                        log.warning(f"Simulation ENTER échouée: {e}")
                        try:
                            a.send_keys(Keys.SPACE)
                            log.info(f"✅ Simulation SPACE réussie avec le sélecteur {i+1}")
                            click_success = True
                        except Exception as e2:
                            log.warning(f"Simulation SPACE échouée: {e2}")
                
                if click_success:
                    link_clicked = True
                    # Vérifier que le téléchargement a bien commencé
                    time.sleep(3)
                    log.info("🔄 Vérification que le téléchargement a commencé...")
                    
                    # Vérifier la présence de fichiers .crdownload (téléchargement en cours)
                    partial_files = list_partial_downloads(DOWNLOAD_DIR)
                    if partial_files:
                        log.info("✅ Téléchargement en cours détecté!")
                    else:
                        log.info("⏳ Attente du début du téléchargement...")
                    
                    break
                else:
                    log.error(f"❌ Toutes les méthodes de clic ont échoué pour le sélecteur {i+1}")
                
            except TimeoutException:
                log.warning(f"Timeout avec le sélecteur {i+1}")
                continue
            except Exception as e:
                log.warning(f"Erreur générale avec le sélecteur {i+1}: {e}")
                continue
        
        # Stratégie 2: Si aucun sélecteur n'a fonctionné, diagnostic approfondi
        if not link_clicked:
            log.warning("❌ Aucun sélecteur standard n'a fonctionné. Diagnostic approfondi...")
            
            try:
                # Attendre beaucoup plus longtemps au cas où la page charge encore
                log.info("Attente supplémentaire pour la génération complète du fichier...")
                time.sleep(20)  # Augmenté de 5 à 20 secondes
                
                # Rechercher TOUS les liens et boutons sur la page
                all_links = driver.find_elements(By.TAG_NAME, "a")
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                all_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                
                log.info(f"Diagnostic: {len(all_links)} liens, {len(all_buttons)} boutons, {len(all_inputs)} inputs trouvés")
                
                # Chercher dans tous les éléments
                all_elements = all_links + all_buttons + all_inputs
                download_candidates = []
                
                for elem in all_elements:
                    try:
                        text = elem.text.lower().strip()
                        href = elem.get_attribute('href') or ""
                        onclick = elem.get_attribute('onclick') or ""
                        title = elem.get_attribute('title') or ""
                        class_name = elem.get_attribute('class') or ""
                        
                        # Chercher des mots-clés de téléchargement
                        download_keywords = ['download', 'télécharger', 'téléchargement', 'export', 'xlsx', 'excel']
                        
                        if any(keyword in text for keyword in download_keywords) or \
                           any(keyword in href.lower() for keyword in download_keywords) or \
                           any(keyword in onclick.lower() for keyword in download_keywords) or \
                           any(keyword in title.lower() for keyword in download_keywords) or \
                           any(keyword in class_name.lower() for keyword in download_keywords):
                            
                            download_candidates.append({
                                'element': elem,
                                'text': text,
                                'href': href,
                                'onclick': onclick,
                                'title': title,
                                'class': class_name,
                                'tag': elem.tag_name
                            })
                    except Exception:
                        continue
                
                log.info(f"Candidats de téléchargement trouvés: {len(download_candidates)}")
                
                # Essayer de cliquer sur les candidats les plus prometteurs
                for i, candidate in enumerate(download_candidates[:5]):  # Essayer les 5 premiers
                    try:
                        elem = candidate['element']
                        log.info(f"Tentative candidat {i+1}: {candidate['tag']} - '{candidate['text']}' - {candidate['href']}")
                        
                        if elem.is_displayed() and elem.is_enabled():
                            # Scroll vers l'élément
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                            time.sleep(1)
                            
                            # Essayer le clic JavaScript d'abord
                            try:
                                driver.execute_script("arguments[0].click();", elem)
                                log.info(f"✅ Clic réussi sur le candidat {i+1}")
                                link_clicked = True
                                break
                            except Exception:
                                # Essayer le clic normal
                                try:
                                    elem.click()
                                    log.info(f"✅ Clic normal réussi sur le candidat {i+1}")
                                    link_clicked = True
                                    break
                                except Exception as e:
                                    log.warning(f"Clic échoué sur candidat {i+1}: {e}")
                        else:
                            log.warning(f"Candidat {i+1} non cliquable (visible: {elem.is_displayed()}, enabled: {elem.is_enabled()})")
                    except Exception as e:
                        log.warning(f"Erreur avec candidat {i+1}: {e}")
                        continue
                        
            except Exception as diag_e:
                log.error(f"Erreur lors du diagnostic approfondi: {diag_e}")
        
        if not link_clicked:
            # Diagnostic final pour aider le débogage
            try:
                log.error("❌ DIAGNOSTIC FINAL ❌")
                page_source_snippet = driver.page_source[:2000]  # Premier 2000 caractères
                log.error(f"Page source (début): {page_source_snippet}")
                
                # Chercher spécifiquement "download-progress"
                if "download-progress" in driver.page_source:
                    log.error("✅ download-progress trouvé dans la page")
                else:
                    log.error("❌ download-progress NON trouvé dans la page")
                    
            except Exception as final_e:
                log.error(f"Erreur lors du diagnostic final: {final_e}")
            
            raise TimeoutException("❌ Impossible de cliquer sur le lien de téléchargement malgré toutes les stratégies.")
            
        log.info(f"Telechargement declenche pour {export_base}")
        
    except Exception as e:
        log.error(f"Erreur lors du declenchement du telechargement pour {export_base}: {e}")
        raise

def download_with_verification(export_base: str, driver, max_retries: int = MAX_RETRIES_PER_FILE) -> bool:
    target_hint = expected_filename_for_today(export_base)
    
    # Moins de tentatives pour les fichiers lourds (pour éviter les timeouts répétés)
    actual_retries = 2 if export_base in HEAVY_FILES else max_retries

    for attempt in range(1, actual_retries + 1):
        log.info(f"Telechargement de {target_hint} (tentative {attempt}/{actual_retries})...")
        cleanup_orphan_crdownload(DOWNLOAD_DIR)

        try:
            trigger_download(export_base, driver)
        except Exception as e:
            log.error(f"Erreur pendant le declenchement du telechargement pour {export_base}: {e}")

        # Utiliser le timeout approprié
        timeout = HEAVY_FILE_TIMEOUT if export_base in HEAVY_FILES else VERIFICATION_TIMEOUT
        path = verify_download_success_for_base(export_base, DOWNLOAD_DIR, timeout=timeout)
        if path:
            file_size = os.path.getsize(path)
            size_mb = file_size / (1024 * 1024)
            log.info("🎉 Telechargement verifie avec succes: %s (%.1f MB)", os.path.basename(path), size_mb)
            return True

        log.warning("Non confirme pour %s (tentative %d)", target_hint, attempt)
        cleanup_orphan_crdownload(DOWNLOAD_DIR)

    log.error("Echec apres %d tentatives pour %s", actual_retries, target_hint)
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

    # Nettoyer les doublons d'abord
    log.info("Nettoyage des fichiers dupliqués...")
    cleanup_duplicate_files(DOWNLOAD_DIR)

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
                log.info(f"📥 Début du téléchargement: {expected_filename_for_today(base)}")
                ok = download_with_verification(base, driver, max_retries=MAX_RETRIES_PER_FILE)
                if ok:
                    successful_downloads += 1
                    log.info(f"✅ Téléchargement réussi pour: {base}")
                else:
                    failed_files.append(base)
                    log.warning(f"❌ Téléchargement échoué pour: {base}")

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
            log.info("🎉 Tous les telechargements (dates %s) termines avec succes !", today_str())
            
            # Vérification finale des fichiers téléchargés
            log.info("=== VERIFICATION FINALE ===")
            final_missing, final_present = check_existing_files(EXPECTED_BASES, DOWNLOAD_DIR)
            
            if not final_missing:
                log.info("✅ VERIFICATION COMPLETE: Tous les fichiers attendus sont presents!")
                
                # Afficher la liste des fichiers téléchargés aujourd'hui
                today_files = []
                for base, files in final_present.items():
                    if files:
                        today_files.extend(files)
                
                log.info(f"📁 Fichiers téléchargés aujourd'hui ({len(today_files)}):")
                for i, filename in enumerate(sorted(today_files), 1):
                    file_path = os.path.join(DOWNLOAD_DIR, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        size_mb = file_size / (1024 * 1024)
                        log.info(f"   {i:2d}. {filename} ({size_mb:.1f} MB)")
                    except Exception:
                        log.info(f"   {i:2d}. {filename}")
            else:
                log.warning(f"⚠️ Attention: {len(final_missing)} fichiers encore manquants: {final_missing}")
                
        else:
            log.warning("⚠️ Telechargements incomplets pour la date %s.", today_str())
            if total_failed > 0:
                failed_list = [expected_filename_for_today(b) for b in files_to_download]
                log.warning(f"❌ Fichiers non téléchargés: {human_list(failed_list)}")

        log.info("📊 STATISTIQUES:")
        log.info("   ✅ Total reussis: %d", total_success)
        log.info("   ❌ Total echoues: %d", total_failed)
        log.info("   ⏱️ Temps total: %dm %ds", int(dt // 60), int(dt % 60))
        
        if total_success > 0:
            avg_time = dt / total_success
            log.info("   📈 Temps moyen par fichier: %.1fs", avg_time)
        
        # Message de fin personnalisé
        if total_failed == 0 and total_success > 0:
            log.info("🎯 MISSION ACCOMPLIE! Tous les téléchargements sont terminés.")
        elif total_success > 0:
            log.info("🔄 PARTIELLEMENT REUSSI. Certains téléchargements ont réussi.")
        else:
            log.info("❌ ECHEC COMPLET. Aucun téléchargement n'a réussi.")
            
        log.info("🔚 Fermeture du navigateur et fin du processus...")
        
        # Petite pause avant fermeture pour laisser le temps de voir les messages
        time.sleep(2)

    finally:
        if own_driver and driver:
            try:
                log.info("🔒 Fermeture du navigateur Chrome...")
                driver.quit()
                log.info("✅ Navigateur fermé avec succès.")
            except Exception as e:
                log.warning(f"⚠️ Erreur lors de la fermeture du navigateur: {e}")
        
        # Message final
        log.info("="*60)
        log.info("🏁 PROCESSUS TERMINE")
        log.info("="*60)

if __name__ == "__main__":
    main_enhanced()
